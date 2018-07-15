using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.RankingModel.SimilarityModels {
    class ListComparer : IEqualityComparer<List<int>> {

        public bool Equals(List<int> x, List<int> y) {
            if (x.Count != y.Count) return false;

            for (int i = 0; i < x.Count; i++) {
                if (x[i] != y[i]) return false;
            }
            return true;
        }

        public int GetHashCode(List<int> obj) {
            int result = 17;
            for (int i = 0; i < obj.Count; i++) {
                unchecked {
                    result = result * 23 + obj[i];
                }
            }
            return result;
        }

    }
}
