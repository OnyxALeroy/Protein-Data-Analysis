import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import Proteins from "../views/Proteins.vue";
import ProteinDetail from "../views/ProteinDetail.vue";
import GraphBuild from "../views/GraphBuild.vue";
import GraphNeighbors from "../views/GraphNeighbors.vue";
import Statistics from "../views/Statistics.vue";
import AnnotationPropagate from "../views/AnnotationPropagate.vue";
import ImportData from "../views/ImportData.vue";
import NotFound from "../views/NotFound.vue";

const routes = [
  { path: "/", name: "Home", component: Home },
  { path: "/proteins", name: "Proteins", component: Proteins },
  {
    path: "/proteins/:proteinId",
    name: "ProteinDetail",
    component: ProteinDetail,
    props: true,
  },
  { path: "/graph/build", name: "GraphBuild", component: GraphBuild },
  {
    path: "/graph/:proteinId/neighbors",
    name: "GraphNeighbors",
    component: GraphNeighbors,
    props: true,
  },
  { path: "/statistics", name: "Statistics", component: Statistics },
  {
    path: "/annotation/propagate",
    name: "AnnotationPropagate",
    component: AnnotationPropagate,
  },
  { path: "/import", name: "ImportData", component: ImportData },
  { path: "/:pathMatch(.*)*", name: "NotFound", component: NotFound },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
