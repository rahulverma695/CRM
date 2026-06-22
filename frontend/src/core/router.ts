import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/login", name: "login", component: () => import("@/pages/LoginPage.vue") },
  { path: "/signup", name: "signup", component: () => import("@/pages/SignupPage.vue") },
  {
    path: "/",
    component: () => import("@/layouts/AppShell.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "dashboard", component: () => import("@/pages/DashboardPage.vue") },
    ],
  },
];

export const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: "login" };
  if ((to.name === "login" || to.name === "signup") && auth.isAuthenticated) {
    return { name: "dashboard" };
  }
  return true;
});
