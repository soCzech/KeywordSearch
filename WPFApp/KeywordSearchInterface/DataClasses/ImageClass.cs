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
        public bool IsHypernym { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Hyponyms { get; set; }
        public string SearchableName { get; set; }
        public int NameLenghtInWords { get; set; }
        public Relevance SearchRelevance { get; set; }

        public string TextRepresentation => SearchableName;

        public int Id => throw new NotImplementedException();

        public bool HasChildren => Hyponyms != null;

        public IEnumerable<int> Children => new List<int>() {7846};

        public int CompareTo(ImageClass other) {
            return (-1) * (((int)SearchRelevance.Bonus + SearchRelevance.NameHits) * 2 / (float)NameLenghtInWords + SearchRelevance.DescriptionHits).CompareTo(
                ((int)other.SearchRelevance.Bonus + other.SearchRelevance.NameHits) * 2 / (float)other.NameLenghtInWords + other.SearchRelevance.DescriptionHits);
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