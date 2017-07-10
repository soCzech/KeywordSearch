using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
// !
using CustomElements;

namespace KeywordSearch {

    class ImageClass : IIdentifiable, IComparable<ImageClass> {
        public string Name { get; set; }
        public string Description { get; set; }
        public string SearchableName { get; set; }
        public int NameLenghtInWords { get; set; }
        public Relevance SearchRelevance { get; set; }

        public int CompareTo(ImageClass other) {
            return (-1) * (((int)SearchRelevance.Bonus + SearchRelevance.NameHits) * 2 / (float)NameLenghtInWords + SearchRelevance.DescriptionHits).CompareTo(
                ((int)other.SearchRelevance.Bonus + other.SearchRelevance.NameHits) * 2 / (float)other.NameLenghtInWords + other.SearchRelevance.DescriptionHits);
        }

        public string GetTextRepresentation() {
            return SearchableName;
        }
    }

    enum NameBonus : byte { None = 0, StartsWord = 1, StartsName = 2, FullName = 10 }

    struct Relevance {
        public byte NameHits { get; set; }
        public byte DescriptionHits { get; set; }
        public NameBonus Bonus { get; set; }
    }

}