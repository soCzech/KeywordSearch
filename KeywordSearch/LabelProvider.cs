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
        public uint Id { get; set; }
        public string SynsetId { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public int NameLenghtInWords { get; set; }

        public int CompareTo(Label other) {
            return Name.CompareTo(other.Name);
        }
    }

    class LabelProvider {

        private string FilePath = ".\\labels_extended.txt";

        public LabelProvider() {
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }
        public LabelProvider(string filePath) {
            FilePath = filePath;
            LoadTask = Task.Factory.StartNew(LoadFromFile);
        }

        private SortedSet<Label> Labels_ = new SortedSet<Label>();

        public Task LoadTask { get; private set; }
        public SortedSet<Label> Labels { get { return (LoadTask.IsCompleted) ? Labels_ : null; } }

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
                        Id = uint.Parse(parts[0]),
                        SynsetId = parts[1],
                        Name = parts[2],
                        Description = parts[3],
                        NameLenghtInWords = minLenght
                    };
                    Labels_.Add(label);
                }
            }
            //Thread.Sleep(5000);
        }

        //public Task LoadFromFileAsync() {
        //    StreamReader reader = new StreamReader(new FileStream(FilePath, FileMode.Open, FileAccess.Read, FileShare.Read, 4096, useAsync: true));
        //    return LoadFromFileAsync(reader).ContinueWith((Task t) => { reader.Dispose(); });
        //}

        //private async Task LoadFromFileAsync(StreamReader reader) {
        //    Task<string> readTask = reader.ReadLineAsync();
        //    string line;

        //    while ((line = await readTask) != null) {
        //        readTask = reader.ReadLineAsync();

        //        var parts = line.Split('~');
        //        if (parts.Length != 4) throw new FormatException("Line has invalid number of parts.");

        //        var label = new Label() { Id = uint.Parse(parts[0]), SynsetId = parts[1], Name = parts[2], Description = parts[3] };
        //        Labels.Add(label);
        //    }
        //}
    }
}
