import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { StorySection } from "@/components/app/story-section";

test("StorySection shows title, subtitle, and the Cognee badge when set", () => {
  render(
    <StorySection title="How it remembers" subtitle="the graph" cognee>
      <div>child</div>
    </StorySection>,
  );
  expect(screen.getByText("How it remembers")).toBeInTheDocument();
  expect(screen.getByText("the graph")).toBeInTheDocument();
  expect(screen.getByText(/Powered by the Cognee knowledge graph/i)).toBeInTheDocument();
  expect(screen.getByText("child")).toBeInTheDocument();
});

test("StorySection hides the badge when cognee is not set", () => {
  render(
    <StorySection title="Proof">
      <div>c</div>
    </StorySection>,
  );
  expect(screen.queryByText(/Powered by the Cognee knowledge graph/i)).toBeNull();
});
