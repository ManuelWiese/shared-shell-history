from textual.widgets import ListItem, ListView


class LazyLoadingListView(ListView):
    """
    A ListView that loads items lazily.

    This ListView subclass is designed
    to load items lazily in batches. It extends the ListView class
    and overrides the `watch_index` method to load more items when the
    index is changed.

    Attributes:
        _full_children (list): A list of all items to be loaded.
        _batch_size (int): The number of items to load in each batch.
    """
    def __init__(
        self,
        *children: ListItem,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        batch_size: int = 64
    ) -> None:
        self._full_children = children
        self._batch_size = batch_size

        super().__init__(
            *children[:2 * self._batch_size],
            initial_index=initial_index,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled
        )

    @property
    def _loaded_items(self):
        """
        The number of items that have been loaded so far.
        """
        return len(self._nodes)

    def watch_index(self, old_index: int | None, new_index: int | None) -> None:
        """
        Watch the index change and load more items if necessary.

        This method is called when the index changes, and it determines
        whether more items need to be loaded based on the new index.

        Args:
            old_index (int): The previous index.
            new_index (int): The new index.
        """
        # Load more items if the new index is valid in the sense
        # that it is within the range of the full children list.
        if new_index is not None and new_index >= 0 and new_index < len(self._full_children):
            if new_index > self._loaded_items:
                # Load enough batches to reach the new index plus at least one more batch
                num_batches_to_load = (new_index - self._loaded_items) // self._batch_size + 2
            elif new_index > self._loaded_items - self._batch_size:
                num_batches_to_load = 1
            else:
                num_batches_to_load = 0

            self._load_batches(num_batches_to_load)

        super().watch_index(
            old_index,
            new_index
        )

    def _load_batches(self, number_of_batches):
        """
        Load a specified number of batches of items.

        This method loads a specified number of batches of items
        from the `_full_children` list. The items are appended to the
        existing list of items in the ListView.

        Args:
            number_of_batches (int): The number of batches to load.
        """
        if self._loaded_items >= len(self._full_children):
            return

        items_to_load = self._full_children[
            self._loaded_items:self._loaded_items + number_of_batches * self._batch_size
        ]

        super().extend(
            items_to_load
        )

    def clear(self):
        """
        Clear the list view and reset the full children list.
        """
        self._full_children = []
        return super().clear()

    def extend(self, items):
        """
        Extend the list view with new items.

        This method extends the list view with new items. If the list view
        is not empty, it raises a NotImplementedError. The case of non-empty
        list views is not needed here so far.

        Args:
            items (list): A list of items to be added to the list view.
        """
        if len(self._full_children) != 0:
            raise NotImplementedError(
                "extend was only implemented for the empty LazyLoadingListView."
            )

        self._full_children.extend(items)
        items_to_load = self._full_children[:2 * self._batch_size]

        return super().extend(
            items_to_load
        )
