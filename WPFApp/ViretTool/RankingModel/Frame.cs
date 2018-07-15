using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ViretTool.RankingModel {
    struct Frame {
        public int Id { get; }
        public float Rank { get; set; }

        public Frame(int id, float rank) {
            Id = id;
            Rank = rank;
        }
    }
}
