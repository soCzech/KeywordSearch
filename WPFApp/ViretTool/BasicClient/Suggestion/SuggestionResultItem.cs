using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.BasicClient.Suggestion {
    class SuggestionResultItem : Controls.IIdentifiable, IComparable<SuggestionResultItem> {

        public Label Label { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Hyponyms { get; set; }
        public Relevance SearchRelevance { get; set; }

        public int Id => Label.SynsetId;
        public string TextRepresentation => Label.Names[0];
        public string TextDescription => Label.Name;

        public bool HasChildren => Label.Hyponyms != null;
        public bool HasOnlyChildren => Label.Id == -1; // is only hypernym
        public IEnumerable<int> Children => Label.Hyponyms;

        public int CompareTo(SuggestionResultItem other) {
            return (-1) * (((int)SearchRelevance.Bonus + SearchRelevance.NameHits) * 2 / (float)Label.NameLenghtInWords + SearchRelevance.DescriptionHits).CompareTo(
                ((int)other.SearchRelevance.Bonus + other.SearchRelevance.NameHits) * 2 / (float)other.Label.NameLenghtInWords + other.SearchRelevance.DescriptionHits);
        }

        public struct Relevance {
            public byte NameHits { get; set; }
            public byte DescriptionHits { get; set; }
            public NameBonus Bonus { get; set; }

            public enum NameBonus : byte { None = 0, StartsWord = 1, StartsName = 2, StartsNameAlone = 4, FullName = 5, FullNameAlone = 10 }
        }
    }
}
