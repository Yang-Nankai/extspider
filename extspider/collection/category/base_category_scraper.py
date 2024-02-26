class BaseCategoryScraper:

    def __init__(self, *args, **kwargs) -> None:
        self.category_name: str = None

    @property
    def BASE_URL(self):
        raise NotImplementedError("BASE_URL must be defined in a subclass")

    @classmethod
    def get_categories(cls) -> list[str]:
        raise NotImplementedError
