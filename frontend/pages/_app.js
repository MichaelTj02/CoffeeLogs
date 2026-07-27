// Global CSS may only be imported here — importing it from a page is a hard build error
// in the pages router.
import "@/styles/globals.css";

import Head from "next/head";

import Navbar from "@/components/Navbar";

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>CoffeeLogs</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Track coffee beans and how you brewed them." />
      </Head>
      <Navbar />
      <main className="container">
        <Component {...pageProps} />
      </main>
    </>
  );
}
