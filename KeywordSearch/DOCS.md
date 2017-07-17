KeywordSearch
=============

Program logic - all references established in constructors of `App`, `MainWindow` and `AppLogic`
```
                             App --> MainWindow
                                         |
     ImageList                           ˅
  (ItemsControl)        ------------ AppLogic --------------
        ˄              |                 |                  |
        |              ˅                 ˅                  ˅
        +------- ImageProvider --> LabelProvider <-- SuggestionProvider
        |             | ˄                |                  ˄
        ˅             | |                ˅                  |
NotFoundMessageBox    | |          classes.labels           |
 (ContentControl)     | |           (label file)            |
                      | |                                   |
       files.index <--   ------- SuggestionTextBox ---------
       (index file)             (custom UI element)
```

---

## Main Classes

##### LabelProvider
```csharp
LabelProvider() // default, path to a label file is ./classes.labels
LabelProvider(string filePath) // custom path to a label file
Dictionary<string, Label> Labels // key is a label name
Task LoadTask // task loading the labels, run automaticaly in constructor
```

##### SuggestionProvider
```csharp
SuggestionProvider(LabelProvider labelProvider)
GetSuggestionsAsync(string filter, SuggestionTextBox suggestionTextBox)
    // creates new task searching through the labels
CancelSuggestionsLookup()
    // task created in GetSuggestionsAsync uses CancellationTokenSource CTS - so cancel it
```

##### ImageProvider
```csharp
ImageProvider(LabelProvider lp) // default, path to a index file is ./files.index
                                // folder of images is ./images/
ImageProvider(LabelProvider lp, string filePath, string folderPath) // custom paths
Search(string filter, SuggestionTextBox suggestionTextBox)
    // does async search and updates ItemsControl.ItemsSource to a new value

ItemsControl ItemsControl // reference to a UI element displaying results (images)
ContentControl NotFoundMessageBox // reference to a UI element displaying errors while search

```

---

## Other Classes

##### BufferedByteStream
```csharp
BufferedByteStream(string filePath) // path to a file
    // used for fast int and float reading
ReadInt64()
ReadInt32()
ReadFloat()
```
