using System;
using System.Collections;
using System.Collections.Generic;

namespace KeywordSearch.TextSearch {
    enum CaseSensitive { No = 0, Yes = 1 }
    class AhoCorasick {

        public AhoCorasick() { }
        public AhoCorasick(CaseSensitive caseSensitivity) {
            CaseSensitivity = caseSensitivity;
        }

        private CaseSensitive CaseSensitivity = CaseSensitive.No;
        private Node Root = new Node();

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

        public void Add(IEnumerable<string> words) {
            foreach (string word in words) {
                Add(word);
            }
        }

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
                    return Children.TryGetValue(letter, out Node node) ? node : null;
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
    }
}
