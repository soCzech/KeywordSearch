using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace KeywordSearchInterface {

    public class LabelProvider {

        private string FilePath = ".\\classes.labels";

        /// <summary>
        /// Asynchronously loads <see cref="Labels"/> from default file.
        /// </summary>
        public LabelProvider() {
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        /// <summary>
        /// Asynchronously loads <see cref="Labels"/> from filePath argument.
        /// </summary>
        /// <param name="filePath">Relative or absolute location of classes.labels file.</param>
        public LabelProvider(string filePath) {
            FilePath = filePath;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private Dictionary<int, Label> Labels_ = new Dictionary<int, Label>();
        private Dictionary<string, List<int>> IdMapping_ = new Dictionary<string, List<int>>();

        /// <summary>
        /// Task responsible for filling <see cref="Labels"/>. Access <see cref="Labels"/> only after completion.
        /// </summary>
        public Task LoadTask { get; private set; }
        /// <summary>
        /// Return dictionary of <see cref="Label"/>s if availible, otherwise null.
        /// </summary>
        public Dictionary<int, Label> Labels { get { return (LoadTask.Status == TaskStatus.RanToCompletion) ? Labels_ : null; } }
        /// <summary>
        /// Return mappings of class names to ids if availible, otherwise null.
        /// </summary>
        public Dictionary<string, List<int>> IdMapping { get { return (LoadTask.Status == TaskStatus.RanToCompletion) ? IdMapping_ : null; } }

        private int[] GetSynsetIds(string text) {
            if (text.Length == 0) return null;
            var parts = text.Split('#');
            var ints = new int[parts.Length];

            for (int i = 0; i < parts.Length; i++) {
                ints[i] = int.Parse(parts[i]);
            }
            return ints;
        }

        private void LoadFromFile() {
            using (StreamReader reader = new StreamReader(FilePath)) {
                string line;

                while ((line = reader.ReadLine()) != null) {
                    var parts = line.Split('~');
                    if (parts.Length != 6) throw new FormatException("Line has invalid number of parts.");

                    var nameParts = parts[2].Split('#');
                    int minLenght = int.MaxValue;
                    foreach (var item in nameParts) {
                        int length = item.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries).Length;
                        if (length < minLenght) minLenght = length;
                    }

                    int id = -1;
                    if (parts[0] != "H") {
                        id = int.Parse(parts[0]);
                    }

                    var label = new Label() {
                        Id = id,
                        SynsetId = int.Parse(parts[1]),
                        Name = string.Join(", ", nameParts),
                        Names = nameParts,
                        Hyponyms = GetSynsetIds(parts[3]),
                        Hypernyms = GetSynsetIds(parts[4]),
                        Description = parts[5],
                        NameLenghtInWords = minLenght
                    };

                    Labels_.Add(label.SynsetId, label);

                    if (!IdMapping_.ContainsKey(label.Name))
                        IdMapping_.Add(label.Name, new List<int> { label.SynsetId });
                    else
                        IdMapping_[label.Name].Add(label.SynsetId);
                }
            }
        }

    }
}
