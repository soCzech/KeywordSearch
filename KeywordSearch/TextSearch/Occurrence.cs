using System;

namespace KeywordSearch.TextSearch {
    /// <summary>
    /// Represents one result form AhoCorasick search.
    /// </summary>
    struct Occurrence {
        public string Word { get; set; }
        public uint StartsAt { get; set; }

        public override string ToString() {
            return string.Format("{0} ({1})", Word, StartsAt);
        }
    }
}
