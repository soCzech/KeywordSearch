using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace KeywordSearch {

    public class Label : IComparable<Label> {
        public int Id { get; set; }
        public string SynsetId { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public int NameLenghtInWords { get; set; }

        public int CompareTo(Label other) {
            return Name.CompareTo(other.Name);
        }
    }

    class LabelProvider {

        private string FilePath = ".\\classes.labels";

        public LabelProvider() {
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        public LabelProvider(string filePath) {
            FilePath = filePath;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private Dictionary<string, Label> Labels_ = new Dictionary<string, Label>();

        public Task LoadTask { get; private set; }
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
                    if (!Labels_.ContainsKey(parts[2]))
                        Labels_.Add(parts[2], label);
                }
            }
        }

    }
}
