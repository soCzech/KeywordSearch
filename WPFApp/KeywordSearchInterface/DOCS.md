Keyword Search Interface
========================

#### Overview

There are three main components of the interface:
- Loading labels: an asynchronous function loads them from a text file.
- Getting suggestions: based on a search phrase, the labels are searched for any matches.
- Providing images: searches for all images satisfying a search phrase.


#### Loading labels

Once you create an instance of `LabelProvider` a standard `Task` `LabelProvider.LoadTask`
is created loading labels from *classes.labels* file.

While loading, all public properties are inaccessible (returning `null`).
When loaded, these properties are availible:
- `Dictionary<int, Label> Labels`{:.language-csharp}
  - mapping *synset id* to its extensive description.
- `Dictionary<string, List<int>> IdMapping`{:.language-csharp}
  - mapping *synset name* to list of *synset id*s with this name.

Even though it is possile to edit the properties, it is safe only to read them.

#### Getting Suggestions

When creating an instance of `SuggestionProvider`, reference to a `LabelProvider` is needed.
The provider has these two public functions implemented from `CustomElements.ISuggestionProvider` interface:
- `void GetSuggestions(string filter)`{:.language-csharp}
    - searches the labels provided by `LabelProvider` by creating a new `Task`.
    - When results ready, `SuggestionResultsReadyEvent` is called with the results as its argument so you need to register proper callback.
    - When resources are not ready or any error occurs `ShowSuggestionMessageEvent` is called with corresponding message.
    - The function regularly checks if the `Task` it is running in is not canceled; and if it is, it stops without any callback.
- `void CancelSuggestions()`{:.language-csharp}
  - calls `Cancel()` on `CancellationTokenSource` of the last `Task` created by `GetSuggestions`.
  - Can be called even if there is no `GetSuggestion` `Task` searching for results - in that case it does nothing.

Only one `GetSuggestions` function (and its `Task`) can be running at any given time in order to be safe since `CancelSuggestions` cancels only the last call of the function.

#### Providing Images

Works the same way as `SuggestionProvider`.
Only impements slightly different interface, but all true for `SuggestionProvider` functions is true for corresponding functions of the `ImageProvider`.

To search images `ImageProvider` needs to load an index file *files.index*. It is done asynchronously by creating a `Task` when creating an instance of `ImageProvider`.

These public functions from `CustomElements.ISearchProvider` interface are implemented:
- `void Search(string filter)`
  - parses a search phrase,
    finds *id*s from *synset name*s in the search phrase by looking into `LabelProvider`,
    and creates sorted list of image names corresponding to the search phrase.
  - When done or when error `SearchResultsReadyEvent` or `ShowSearchMessageEvent` respectively is called similarly to `SuggestionProvider`.
  - It is safe to call even if loading of labels in `LabelProvider` or loading of the index file is not completed - `ShowSearchMessageEvent` with proper message is called.
- `void CancelSearch()`
  - works similarly to `SuggestionProvider`.

Only one `Search` function (and its `Task`) can be running at any given time in order to be safe since `CancelSearch` cancels only the last call of the function.
