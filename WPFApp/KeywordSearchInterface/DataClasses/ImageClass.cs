using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
// !
using CustomElements;

namespace KeywordSearchInterface {

    /// <summary>
    /// Used for SearchTextBox suggestions.
    /// </summary>
    public class ImageClass : IIdentifiable, IComparable<ImageClass> {
        public Label Label { get; set; }
        public bool IsHypernym => Label.Id == -1;
        public string Name { get; set; }
        public string Description { get; set; }
        public string Hyponyms { get; set; }
        public Relevance SearchRelevance { get; set; }

        public string TextRepresentation { get; set; }
        public int Id => Label.SynsetId;
        public bool HasChildren => Label.Hyponyms != null;
        public IEnumerable<int> Children => Label.Hyponyms;

        public int CompareTo(ImageClass other) {
            return (-1) * (((int)SearchRelevance.Bonus + SearchRelevance.NameHits) * 2 / (float)Label.NameLenghtInWords + SearchRelevance.DescriptionHits).CompareTo(
                ((int)other.SearchRelevance.Bonus + other.SearchRelevance.NameHits) * 2 / (float)other.Label.NameLenghtInWords + other.SearchRelevance.DescriptionHits);
        }

    }

    /// <summary>
    /// Adds bonus when calculating relevance of a search phrase
    /// </summary>
    public enum NameBonus : byte { None = 0, StartsWord = 1, StartsName = 2, StartsNameAlone = 4, FullName = 5, FullNameAlone = 10 }

    public struct Relevance {
        public byte NameHits { get; set; }
        public byte DescriptionHits { get; set; }
        public NameBonus Bonus { get; set; }
    }

}