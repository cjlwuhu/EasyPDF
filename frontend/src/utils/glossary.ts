export function removeGlossaryTerm<T extends { id: number }>(terms: T[], termId: number): T[] {
  return terms.filter((term) => term.id !== termId);
}

export function describeGlossaryDeleteError(error: unknown): string {
  if (error instanceof TypeError) {
    return "Backend is unavailable. Start EasyPDF and try again.";
  }
  return error instanceof Error ? error.message : "Failed to delete glossary term";
}
