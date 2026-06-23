import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import BaseButton from "./BaseButton.vue";

describe("BaseButton", () => {
  it("renders slot content", () => {
    const wrapper = mount(BaseButton, { slots: { default: "Save" } });
    expect(wrapper.text()).toBe("Save");
  });

  it("defaults to primary accent styling", () => {
    const wrapper = mount(BaseButton, { slots: { default: "Go" } });
    expect(wrapper.classes()).toContain("bg-accent");
  });

  it("applies ghost styling when variant=ghost", () => {
    const wrapper = mount(BaseButton, {
      props: { variant: "ghost" }, slots: { default: "Cancel" },
    });
    expect(wrapper.classes()).toContain("bg-transparent");
  });
});
