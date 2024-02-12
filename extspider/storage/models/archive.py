# -*- coding: utf-8 -*-


from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy import (ForeignKey, Date, String, BigInteger, JSON, Boolean,
                        Integer, select)
from sqlalchemy.orm import (Mapped, mapped_column, column_property,
                            relationship, validates)
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.sql.functions import current_date
from sqlalchemy.sql.expression import or_, case, null
from sqlalchemy.ext.hybrid import hybrid_property

from extspider.storage.models.common import BaseModel


class Archive(BaseModel):
    """
    Archive file containing extension-related scripts and resources
    """
    __tablename__ = "archives"

    digest: Mapped[str] = mapped_column(String(16), primary_key=True)
    extension_id: Mapped[str] = mapped_column(
        ForeignKey("extensions.id")
    )
    manifest: Mapped[Optional[Dict]] = mapped_column(JSON)
    download_date: Mapped[date] = mapped_column(Date(),
                                                server_default=current_date())
    is_corrupted: Mapped[Optional[bool]] = mapped_column(Boolean)
    byte_size: Mapped[Optional[int]] = mapped_column(BigInteger)

    extension: Mapped["Extension"] = relationship(back_populates="archives")
    fingerprints: Mapped[list["Fingerprint"]] = relationship(
        back_populates="archive"
    )

    def __init__(self,
                 digest:Optional[str]=None,
                 extension_id:Optional[str]=None,
                 **kw:Any) -> None:
        super().__init__(**kw)
        if digest is not None:
            self.digest = digest
        if extension_id is not None:
            self.extension_id = extension_id

    @validates("byte_size")
    def validate_byte_size(self, _, byte_size: int) -> int:
        if byte_size <= 0:
            raise ValueError(
                "The byte size of the crx archive cannot be " \
                + f"{byte_size}; Expected a number greater than zero."
            )

        return byte_size

    @hybrid_property
    def is_vulnerable(self) -> bool:
        if self.manifest_version is None:
            return False

        for fingerprint in self.fingerprints:
            if fingerprint.is_vulnerable:
                return True

        return False

    @hybrid_property
    def manifest_version(self) -> Optional[int]:
        if self.manifest is None:
            return None
        return self.manifest.get("manifest_version")

    @manifest_version.expression
    def manifest_version(cls) -> Optional[int]:
        return cls.manifest.op("->>")("manifest_version").cast(Integer)


    @hybrid_property
    def version_name(self) -> Optional[str]:
        if self.manifest is None:
            return None

        return self.manifest.get("version_name",
                                 self.manifest.get("version"))

    @version_name.expression
    def version_name(cls) -> Optional[str]:
        # return cls.manifest.op("->>")("version_name")
        return case(
            (cls.manifest.op("->>")("version_name") == null(),
             cls.manifest.op("->>")("version")),
             else_=cls.manifest.op("->>")("version_name")
        ).cast(String)


class Fingerprint(BaseModel):
    """
    Fingerprint a web-accessible resource extracted from a crx archive
    """
    __tablename__ = "fingerprints"

    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_digest:Mapped[str] = mapped_column(ForeignKey(Archive.digest))
    resource:Mapped[str]
    match_pattern:Mapped[Optional[str]] = mapped_column(default=None)

    archive:Mapped[Archive] = relationship(back_populates="fingerprints")
    extension_id:Mapped[str] = column_property(
        select(Archive.extension_id)
        .where(Archive.digest == archive_digest)
        .correlate_except(Archive)
        .scalar_subquery()
    )


    # @hybrid_property
    # def extension_id(self) -> str:
    #     return self.archive.extension_id


    # @extension_id.expression
    # def extension_id(cls) -> str:
    #     return cls.archive.extension_id


    @hybrid_property
    def manifest(self) -> Optional[dict]:
        return self.archive.manifest


    @hybrid_property
    def manifest_version(self) -> Optional[int]:
        if self.manifest is None:
            return None

        return self.manifest.get("manifest_version")


    @hybrid_property
    def is_vulnerable(self) -> bool:
        return (
            self.manifest_version == 2
            or self.match_pattern == "<all_urls>"
            or self.match_pattern == "*://*/*"
            or self.match_pattern == "https://*/*"
            # or self.match_pattern == "http://*/*"
            #
            # ^ from a fingerprinter's perspective, it is not possible to
            #   access http and https restriced resources contemporarily.
            #   Thus, http was excluded as it is a less common constraint
        )


    @is_vulnerable.expression
    def is_vulnerable(cls) -> bool:

        return or_(
            cls.archive.has(Archive.manifest_version == 2),
            cls.match_pattern == "<all_urls>",
            cls.match_pattern == "*://*/*",
            cls.match_pattern == "https://*/*",
            cls.match_pattern == "http://*/*"
        )
