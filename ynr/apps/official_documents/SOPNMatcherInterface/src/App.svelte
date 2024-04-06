<script>
    import PdfPage from "./lib/PdfPage.svelte";
    import * as pdfjs from "pdfjs-dist";
    import {BallotStore} from "./lib/Store.js"
    import {derived} from "svelte/store";

    pdfjs.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.0.379/pdf.worker.min.mjs';

    export let ballots;
    $BallotStore = ballots

    export let sopn_pdf;

    var documentLoader = pdfjs.getDocument(sopn_pdf).promise;

    export const transformedBallotsStore = derived(BallotStore, $BallotStore => {
        return JSON.stringify($BallotStore);
    });

</script>

<main class="ds-stack">
    {#await documentLoader}
        <p>Loading PDF</p>
    {:then pdf_document}
        <p>This document has <strong>{pdf_document.numPages} pages</strong> and the elections has
            <strong>{ballots.length} ballots</strong>.
        </p>
        <p>Note: only mark the <em>first</em> page for each ballot. Continuation pages will get detected automatically.
        </p>

        {#each Array(pdf_document.numPages) as _, page_number}
            <PdfPage page="{pdf_document.getPage(page_number+1)}" page_number="{page_number}"
                     total_pages="{pdf_document.numPages}"/>
        {/each}
        <form method="post">

            <input type="hidden" name="matched_pages" id="matched_pages" value="{$transformedBallotsStore}">
            <button type="submit" class="ds-button">Save</button>
        </form>
    {:catch error}
        Error: {error}
    {/await}
</main>
