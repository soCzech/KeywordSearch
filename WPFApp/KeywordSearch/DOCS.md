Keyword Search
==============

#### Program logic

All references established in constructor of `MainWindow`.

```
     ImageList                          App
  (ItemsControl)                         |
        ˄                                ˅
        +--------------+----------- MainWindow --------------
        |              |             ˄   |                  |
        |              |     _______/    |                  |
        |              ˅    /            ˅                  ˅
        |        ImageProvider --> LabelProvider <-- SuggestionProvider
        ˅             | ˄                |            /     ˄
NotFoundMessageBox    | |                ˅           /      |
 (ContentControl)     | |          classes.labels   /       |
                      | |           (label file)   /        |
                      | |                         ˅         |
       files.index <--   ------- SuggestionTextBox ---------
       (index file)             (custom UI element)


        Legend:   | or -- ... reference
                  / or __ ... delegate to a function
```

#### Example flow

```
           STARTUP             SUGGESTIONS                    SEARCH

              +-- ImageProvider
             /    > LoadFromFile()
            /
           +-- LabelProvider
          /    > LoadFromFile()
         /
        /                +-- SearchProvider ---+        +-- ImageProvider --+
       /                /    > GetSuggestions() \      /    > Search()       \
      /                /                         \    /                       \
App -+-- MainWindow --+-------- UI Thread --------+--+------- UI Thread -------+-- END
```
