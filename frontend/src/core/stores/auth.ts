import { defineStore } from "pinia";
import { api } from "@/core/api";

interface TokenPair { access_token: string; refresh_token: string }
interface User { id: string; tenant_id: string; email: string; name: string; role: string }

const ACCESS = "access_token";
const REFRESH = "refresh_token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS) as string | null,
    refreshToken: localStorage.getItem(REFRESH) as string | null,
    user: null as User | null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.accessToken,
  },
  actions: {
    setTokens(t: TokenPair) {
      this.accessToken = t.access_token;
      this.refreshToken = t.refresh_token;
      localStorage.setItem(ACCESS, t.access_token);
      localStorage.setItem(REFRESH, t.refresh_token);
    },
    async signup(payload: { company_name: string; name: string; email: string; password: string }) {
      this.setTokens(await api<TokenPair>("/auth/signup", { method: "POST", body: payload }));
      await this.fetchMe();
    },
    async login(email: string, password: string) {
      this.setTokens(await api<TokenPair>("/auth/login", { method: "POST", body: { email, password } }));
      await this.fetchMe();
    },
    async fetchMe() {
      this.user = await api<User>("/auth/me", { token: this.accessToken });
    },
    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      localStorage.removeItem(ACCESS);
      localStorage.removeItem(REFRESH);
    },
  },
});
