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

        private Dictionary<string, Label> Labels_ = new Dictionary<string, Label>();

        /// <summary>
        /// Task responsible for filling <see cref="Labels"/>. Access <see cref="Labels"/> only after completion.
        /// </summary>
        public Task LoadTask { get; private set; }
        /// <summary>
        /// Return dictionary of <see cref="Label"/>s if availible, otherwise null.
        /// </summary>
        public Dictionary<string, Label> Labels { get { return (LoadTask.Status == TaskStatus.RanToCompletion) ? Labels_ : null; } }

        private void LoadFromFile() {
            using (StreamReader reader = new StreamReader(FilePath)) {
                string line;

                while ((line = reader.ReadLine()) != null) {
                    var parts = line.Split('~');
                    if (parts.Length != 4) throw new FormatException("Line has invalid number of parts.");

                    var nameParts = parts[2].Split(',');
                    int minLenght = int.MaxValue;
                    foreach (var item in nameParts) {
                        int length = item.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries).Length;
                        if (length < minLenght) minLenght = length;
                    }

                    var label = new Label() {
                        Id = int.Parse(parts[0]),
                        SynsetId = parts[1],
                        Name = parts[2],
                        Description = parts[3],
                        NameLenghtInWords = minLenght
                    };
                    //if (Labels_.ContainsKey(parts[2]))
                    //    throw new Exception();
                    // TODO !!!
                    // Make sure the label file contains unique class names
                    if (!Labels_.ContainsKey(parts[2]))
                        Labels_.Add(parts[2], label);
                }
            }
        }

    }
}
