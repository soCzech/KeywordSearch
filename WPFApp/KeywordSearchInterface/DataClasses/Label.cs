using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace KeywordSearchInterface {

    public class Label : IComparable<Label> {
        public int Id { get; set; }
        public int SynsetId { get; set; }
        public string Name { get; set; }
        public string[] Names { get; set; }
        public int[] Hyponyms { get; set; }
        public int[] Hypernyms { get; set; }
        public string Description { get; set; }
        public int NameLenghtInWords { get; set; }

        public int CompareTo(Label other) {
            return Name.CompareTo(other.Name);
        }
    }

}
