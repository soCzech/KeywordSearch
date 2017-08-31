using System;

namespace KeywordSearchInterface {

    /// <summary>
    /// A struct with all the file info needed to sort and display images.
    /// </summary>
    public struct Filename : IComparable<Filename> {
        public uint Id { get; set; }
        public float Probability { get; set; }

        public int CompareTo(Filename other) {
            return -Probability.CompareTo(other.Probability);
        }
    }

}
