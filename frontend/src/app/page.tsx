/**
 * Home page - redirects to signup page.
 * New users should land on signup, not signin.
 */

import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to signup page for new users
  redirect("/signup");
}
