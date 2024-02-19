# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql.functions import current_date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Date, Numeric, ForeignKey, JSON, BigInteger, Integer, case, null, PrimaryKeyConstraint

from extspider.storage.models.common import BaseModel
from extspider.common.utils import is_valid_extension_id


class ExtensionPermission(BaseModel):
    """
    ExtensionPermission extension permissions botained from the Extension manifest
    """
    __tablename__ = "extension_permissions"

    extension_id: Mapped[str] = mapped_column()
    extension_version: Mapped[str] = mapped_column()
    manifest_version: Mapped[Optional[int]]
    permissions: Mapped[Optional[List]] = mapped_column(JSON)
    optional_permissions: Mapped[Optional[List]] = mapped_column(JSON)
    content_scripts_matches: Mapped[Optional[List]] = mapped_column(JSON)
    host_permissions: Mapped[Optional[List]] = mapped_column(JSON)
    optional_host_permissions: Mapped[Optional[List]] = mapped_column(JSON)

    # Define a composite primary key using PrimaryKeyConstraint
    __table_args__ = (
        PrimaryKeyConstraint('extension_id', 'extension_version'),
    )

    # extension: Mapped["Extension"] = relationship(back_populates="permission")

    def __init__(self, extension_id: Optional[str] = None,
                 extension_version: Optional[str] = None,
                 **kw: Any) -> None:
        super().__init__(**kw)

        if extension_id is not None:
            self.extension_id = extension_id

        if extension_version is not None:
            self.extension_version = extension_version

    @validates("manifest_version")
    def validate_manifest_version(self, _, mainfest_version: int) -> int:
        if int(mainfest_version) != 2 and int(mainfest_version) != 3:
            raise ValueError(
                "The manifest version of the crx cannot be " \
                + f"{mainfest_version}; Expected a number 2 or 3."
            )
        return int(mainfest_version)

    @validates("extension_id")
    def validate_extension_id(self, _, id: str) -> str:
        # key and id are expected to be the same value
        is_valid = is_valid_extension_id(id)

        if not is_valid:
            raise ValueError(f"The provided extension identifier '{id} is invalid'."
                             f"Only [a-p]*32 are allowed.")

        return id
