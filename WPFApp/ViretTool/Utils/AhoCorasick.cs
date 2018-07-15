using System;
using System.Collections;
using System.Collections.Generic;

namespace ViretTool.Utils {

    /// <summary>
    /// AhoCorasick text search algorithm
    /// </summary>
    class AhoCorasick {

        /// <summary>
        /// Perform case sensitive search
        /// </summary>
        public enum CaseSensitive { No = 0, Yes = 1 }

        /// <summary>
        /// Default is case insensitive search
        /// </summary>
        public AhoCorasick() { }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="caseSensitivity">Case sensitivity of a seach</param>
        public AhoCorasick(CaseSensitive caseSensitivity) {
            CaseSensitivity = caseSensitivity;
        }

        private Node Root = new Node();
        private CaseSensitive CaseSensitivity = CaseSensitive.No;

        /// <summary>
        /// Add a word to a set of searched words
        /// </summary>
        /// <param name="word">A word to search for</param>
        public void Add(string word) {
            if (CaseSensitivity == CaseSensitive.No)
                word = word.ToLower();

            var node = Root;
            foreach (char l in word) {
                if (node[l] == null)
                    node[l] = new Node(l);
                node = node[l];
            }
            node.Hit = word;
        }

        /// <summary>
        /// Add multiple words at once to a set of searched words
        /// </summary>
        /// <param name="words">Words to search for</param>
        public void Add(IEnumerable<string> words) {
            foreach (string word in words) {
                Add(word);
            }
        }

        /// <summary>
        /// Build a search tree, run before <see cref="Find(string)"/>
        /// </summary>
        public void Build() {
            var queue = new Queue<Node>();
            Root.Fail = Root;
            Root.Jump = null;

            foreach (var child in Root) {
                child.Fail = Root;
                child.Jump = null;
                queue.Enqueue(child);
            }

            while (queue.Count > 0) {
                var node = queue.Dequeue();

                foreach (var child in node) {
                    var fallBack = node.Fail;
                    while (fallBack[child.Letter] == null && fallBack != Root)
                        fallBack = fallBack.Fail;

                    fallBack = fallBack[child.Letter] ?? Root;
                    child.Fail = fallBack;

                    if (fallBack.Hit != null) child.Jump = fallBack;
                    else child.Jump = fallBack.Jump;

                    queue.Enqueue(child);
                }
            }
        }

        /// <summary>
        /// Runs AC algorithm on a given text
        /// </summary>
        /// <param name="text">A text to search in</param>
        /// <returns>Found positions</returns>
        public IEnumerable<Occurrence> Find(string text) {
            uint endsAt = 1;
            var node = Root;
            if (CaseSensitivity == CaseSensitive.No)
                text = text.ToLower();

            foreach (char l in text) {
                while(node[l] == null && node != Root)
                    node = node.Fail;
                node = node[l] ?? Root;

                if (node.Hit != null)
                    yield return new Occurrence { Word = node.Hit, StartsAt = (uint)(endsAt - node.Hit.Length) };

                while (node.Jump != null) {
                    node = node.Jump;
                    yield return new Occurrence { Word = node.Hit, StartsAt = (uint)(endsAt - node.Hit.Length) };
                }
                endsAt++;
            }
        }


        private class Node : IEnumerable<Node> {

            public Node() { }

            public Node(char letter) {
                Letter = letter;
            }

            private Dictionary<char, Node> Children = new Dictionary<char, Node>();
            
            public char Letter { get; private set; }
            public Node Fail { get; set; }
            public Node Jump { get; set; }
            public string Hit { get; set; }

            public Node this[char letter] {
                get {
                    Node node;
                    return Children.TryGetValue(letter, out node) ? node : null;
                }
                set {
                    Children[letter] = value;
                }
            }

            public IEnumerator<Node> GetEnumerator() {
                return Children.Values.GetEnumerator();
            }

            IEnumerator IEnumerable.GetEnumerator() {
                return GetEnumerator();
            }
        }

        /// <summary>
        /// Represents one result form AhoCorasick search
        /// </summary>
        public struct Occurrence {
            /// <summary>
            /// Found word
            /// </summary>
            public string Word { get; set; }
            /// <summary>
            /// Position of the word in a text
            /// </summary>
            public uint StartsAt { get; set; }

            public override string ToString() {
                return string.Format("{0} ({1})", Word, StartsAt);
            }
        }
    }
}
