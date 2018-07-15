using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.RankingModel.SimilarityModels {
    class IDFLoader {
        static byte[] HeaderBytes = Encoding.ASCII.GetBytes("BC\0\0\0\0\0\0\0\0\0\0\0\0\0\02018-04-01 00:00:00\n");

        public static float[] LoadFromFile(string filePath) {
            float[] IDF = null;

            using (BinaryReader stream = new BinaryReader(File.OpenRead(filePath))) {
                var header = stream.ReadBytes(HeaderBytes.Length);
                for (int i = 0; i < HeaderBytes.Length; i++) {
                    if (header[i] != HeaderBytes[i]) throw new Exception("Header mismatch!");
                }
                int dimension = stream.ReadInt32();
                IDF = new float[dimension];

                float max = float.MinValue;
                for (int i = 0; i < dimension; i++) {
                    IDF[i] = stream.ReadSingle();

                    if (max < IDF[i]) max = IDF[i];
                }

                for (int i = 0; i < dimension; i++) {
                    IDF[i] = (float)Math.Log(max / IDF[i]) + 1;
                }
            }

            return IDF;
        }

    }
}
