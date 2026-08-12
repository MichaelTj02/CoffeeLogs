// Global CSS may only be imported here; importing it from a page is a hard build error.
import "@/styles/globals.css";

import Head from "next/head";

import AuthGuard from "@/components/AuthGuard";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth";

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Head>
        <title>CoffeeLogs</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Track coffee beans and how you brewed them." />
      </Head>
      <Navbar />
      <main className="container">
        <AuthGuard>
          <Component {...pageProps} />
        </AuthGuard>
      </main>
    </AuthProvider>
  );
}
