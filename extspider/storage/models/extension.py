# -*- coding: utf-8 -*-

from typing import Optional, List, Any, Dict
from decimal import Decimal
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql.functions import current_date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Date, Numeric, ForeignKey, JSON, BigInteger, Integer, case, null

from extspider.storage.models.common import BaseModel


class ExtensionCategory(BaseModel):
    """
    ExtensionCategory extension categories obtained from the Chrome web store
    """
    __tablename__ = "extension_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)

    extensions: Mapped[List["Extension"]] = relationship(
        back_populates="category"
    )

    def __init__(self, name: Optional[str] = None, **kw: Any) -> None:
        super().__init__(**kw)

        if name is not None:
            self.name = name


class Extension(BaseModel):
    """
    Extension software module customising functionality of the Google Chrome
    browser
    """
    __tablename__ = "extensions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[Optional[str]]
    developer_name: Mapped[Optional[str]]
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("extension_categories.id")
    )
    download_count: Mapped[Optional[int]]
    rating_count: Mapped[Optional[int]]
    rating_average: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2)
    )
    manifest: Mapped[Optional[Dict]] = mapped_column(JSON)
    # TODO: byte_size 这里的类型是int还是float?
    byte_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    latest_version: Mapped[Optional[str]]
    updated_at: Mapped[Optional[date]]
    download_date: Mapped[Date] = mapped_column(Date(),
                                                server_default=current_date(),
                                                onupdate=current_date())
    # permissions: Mapped[List["ExtensionPermission"]] = relationship(back_populates="extension")
    # permission: Mapped["ExtensionPermission"] = relationship(uselist=False, back_populates='extension')
    category: Mapped["ExtensionCategory"] = relationship(
        back_populates="extensions"
    )

    def __init__(self,
                 extension_id: Optional[str] = None,
                 category: Optional[ExtensionCategory] = None,
                 **kw: Any) -> None:
        super().__init__(**kw)
        if extension_id is not None:
            self.id = extension_id
        if category is not None:
            self.category = category

    @hybrid_property
    def category_name(self) -> Optional[str]:
        """category_name

        Returns:
            str: the category associate with the extension; None if not set
        """
        if self.category_id is None:
            return None

        return self.category.name

    @validates("id")
    def validate_id(self, _, id: str) -> str:
        # key and id are expected to be the same value
        if len(id) != 32:
            raise ValueError(f"An extension identifier of length {len(id)} " \
                             + "was provided; Expected 32 characters.")

        found_invalid_characters = self.get_invalid_characters_from_id(id)
        if len(found_invalid_characters) > 0:
            raise ValueError(
                f"The provided extension identifier '{id}' contains invalid " \
                + f"characters: {found_invalid_characters}; Only characters " \
                + "[a-p] are allowed."
            )

        return id

    @validates("download_count")
    def validate_download_count(self, _, download_count: int) -> int:
        if download_count is None:
            return

        if download_count < 0:
            raise ValueError(
                f"The provided download count '{download_count}' is negative."
            )

        return download_count

    @validates("rating_count")
    def validate_rating_count(self, _, rating_count: int) -> int:
        if rating_count is None:
            return

        if rating_count < 0:
            raise ValueError(
                f"The provided rating count '{rating_count}' is negative."
            )

        return rating_count

    @validates("rating_average")
    def validate_rating_average(self, _,
                                rating_average: Decimal) -> Decimal:
        if rating_average is None:
            return

        if rating_average < 0 or rating_average > 5:
            raise ValueError(
                f"The provided rating average '{rating_average}' is " \
                + "invalid; Expected a value between the [0, 5] interval."
            )

        return rating_average

    @validates("byte_size")
    def validate_byte_size(self, _, byte_size: int) -> int:
        if byte_size <= 0:
            raise ValueError(
                "The byte size of the crx archive cannot be " \
                + f"{byte_size}; Expected a number greater than zero."
            )

        return byte_size

    @hybrid_property
    def manifest_version(self) -> Optional[int]:
        if self.manifest is None:
            return None
        return self.manifest.get("manifest_version")

    @manifest_version.expression
    def manifest_version(cls) -> Optional[int]:
        return cls.manifest.op("->>")("manifest_version").cast(Integer)

    @hybrid_property
    def manifest_permissions(self) -> Optional[List]:
        if self.manifest is None:
            return None
        return self.manifest.get("permissions")

    @manifest_permissions.expression
    def manifest_permissions(cls) -> Optional[int]:
        return cls.manifest.op("->>")("permissions").cast(list)

    @hybrid_property
    def manifest_optional_permissions(self) -> Optional[List]:
        if self.manifest is None:
            return None
        return self.manifest.get("optional_permissions")

    @manifest_optional_permissions.expression
    def manifest_optional_permissions(cls) -> Optional[int]:
        return cls.manifest.op("->>")("optional_permissions").cast(list)

    @hybrid_property
    def manifest_content_scripts_matches(self) -> Optional[List]:
        if self.manifest is None:
            return None
        return self.manifest.get("content_scripts.matches")

    @manifest_content_scripts_matches.expression
    def manifest_content_scripts_matches(cls) -> Optional[int]:
        return cls.manifest.op("->>")("content_scripts.matches").cast(list)

    @hybrid_property
    def manifest_host_permissions(self) -> Optional[List]:
        if self.manifest is None:
            return None
        return self.manifest.get("host_permissions")

    @manifest_host_permissions.expression
    def manifest_host_permissions(cls) -> Optional[int]:
        return cls.manifest.op("->>")("host_permissions").cast(list)

    @hybrid_property
    def manifest_optional_host_permissions(self) -> Optional[List]:
        if self.manifest is None:
            return None
        return self.manifest.get("optional_host_permissions")

    @manifest_optional_host_permissions.expression
    def manifest_optional_host_permissions(cls) -> Optional[int]:
        return cls.manifest.op("->>")("optional_host_permissions").cast(list)

    @hybrid_property
    # TODO: version_name or version, 有点是version_name有的是version，因此都需要
    def version_name(self) -> Optional[str]:
        if self.manifest is None:
            return None

        return self.manifest.get("version_name",
                                 self.manifest.get("version"))

    @version_name.expression
    def version_name(cls) -> Optional[str]:
        return case(
            (cls.manifest.op("->>")("version_name") == null(),
             cls.manifest.op("->>")("version")),
            else_=cls.manifest.op("->>")("version_name")
        ).cast(String)

    @staticmethod
    def get_invalid_characters_from_id(id: str) -> str:
        valid_characters = "abcdefghijklmnop"
        unexpected_characters = ""
        for character in id:
            if character not in valid_characters:
                unexpected_characters += character

        return unexpected_characters
