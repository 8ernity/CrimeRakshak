"use server";
import { redirect } from "next/navigation";

export async function setUserRole(role: string) {
  // Clerk is removed, auth handled manually.
  // After setting the role, send them to the overview dashboard
  redirect("/overview");
}
