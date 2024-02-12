# -*- coding: utf-8 -*-

from typing import Optional, List, Any
from decimal import Decimal
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql.functions import current_date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import String, Date, Numeric, ForeignKey

from extspider.storage.models.common import BaseModel


class ExtensionCategory(BaseModel):
    """
    ExtensionCategory extension categories obtained from the chrome web store
    """
    __tablename__ = "extension_categories"

    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str] = mapped_column(String(128), unique=True)

    extensions:Mapped[List["Extension"]] = relationship(
        back_populates="category"
    )

    def __init__(self, name:Optional[str]=None, **kw:Any) -> None:
        super().__init__(**kw)

        if name is not None:
            self.name = name


class Extension(BaseModel):
    """
    Extension software module customising functionality of the Google Chrome
    browser
    """
    __tablename__ = "extensions"

    id:Mapped[str] = mapped_column(String(32), primary_key=True)
    name:Mapped[Optional[str]]
    category_id:Mapped[Optional[int]] = mapped_column(
        ForeignKey("extension_categories.id")
    )
    download_count:Mapped[Optional[int]]
    rating_count:Mapped[Optional[int]]
    rating_percentage:Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2)
    )
    latest_version:Mapped[Optional[str]]
    updated_at:Mapped[date] = mapped_column(Date(),
                                            server_default=current_date(),
                                            onupdate=current_date())

    archives:Mapped[List["Archive"]] = relationship(back_populates="extension")
    category:Mapped["ExtensionCategory"] = relationship(
        back_populates="extensions"
    )


    def __init__(self,
                 extension_id:Optional[str]=None,
                 category:Optional[ExtensionCategory]=None,
                 **kw:Any) -> None:
        super().__init__(**kw)
        if extension_id is not None:
            self.id = extension_id
        if category is not None:
            self.category = category



    @hybrid_property
    def rating_stars(self) -> Optional[float]:
        """rating_stars computes 5-star rating from the percentage score

        Returns:
            Optional[float]: The extension's overall rating; None if no reviews
            were awarded
        """
        if self.rating_percentage is None:
            return None

        return self.rating_percentage / 100 * 5


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
    def validate_id(self, _, id:str) -> str:
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
    def validate_download_count(self, _, download_count:int) -> int:
        if download_count is None:
            return

        if download_count < 0:
            raise ValueError(
                f"The provided download count '{download_count}' is negative."
            )

        return download_count


    @validates("rating_count")
    def validate_rating_count(self, _, rating_count:int) -> int:
        if rating_count is None:
            return

        if rating_count < 0:
            raise ValueError(
                f"The provided rating count '{rating_count}' is negative."
            )

        return rating_count


    @validates("rating_percentage")
    def validate_rating_percentage(self, _,
                                   rating_percentage:Decimal) -> Decimal:
        if rating_percentage is None:
            return

        if rating_percentage < 20 or rating_percentage > 100:
            raise ValueError(
                f"The provided rating percentage '{rating_percentage}' is " \
                + "invalid; Expected a value between the [0, 100] interval."
            )

        return rating_percentage



    @staticmethod
    def get_invalid_characters_from_id(id:str) -> str:
        valid_characters = "abcdefghijklmnop"
        unexpected_characters = ""
        for character in id:
            if character not in valid_characters:
                unexpected_characters += character

        return unexpected_characters
