using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.RankingModel.SimilarityModels {
    class KeywordModelWrapper {
        private Dictionary<string, KeywordModel> mKeywordModels = new Dictionary<string, KeywordModel>();

        public KeywordModelWrapper(string[] indexFiles, string[] idfFiles, string[] sourceNames) {

            for (int i = 0; i < indexFiles.Length; i++) {
                KeywordModel model = new KeywordModel(indexFiles[i], idfFiles[i]);
                mKeywordModels.Add(sourceNames[i], model);
            }
        }

        public List<Frame> RankFramesBasedOnQuery(List<List<int>> queryKeyword, string source) {
            return mKeywordModels[source].RankFramesBasedOnQuery(queryKeyword);
        }
    }
}
