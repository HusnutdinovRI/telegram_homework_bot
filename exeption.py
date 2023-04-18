class EmptyListError(Exception):
    """Исключение возникающее если список пуст."""

    def __init__(self, text):
        """Магический метод для инцициазиции."""
        self.txt = text
