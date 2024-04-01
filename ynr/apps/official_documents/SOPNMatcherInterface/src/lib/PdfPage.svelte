<script>
    import BallotPicker from "./BallotPicker.svelte";

    export let page_number;
    export let total_pages;
    export let page;

    function render_page(element, {loaded_page}) {
        var scale = 1.5;
        var viewport = loaded_page.getViewport({scale: scale,});
// Support HiDPI-screens.
        var outputScale = window.devicePixelRatio || 1;

        var canvas = element;
        var context = canvas.getContext('2d');

        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = "100%";
        // canvas.style.width = Math.floor(viewport.width) + "px";
        // canvas.style.height = Math.floor(viewport.height) + "px";
        // canvas.style.height = Math.floor(viewport.height) + "px";

        var transform = outputScale !== 1
            ? [outputScale, 0, 0, outputScale, 0, 0]
            : null;

        var renderContext = {
            canvasContext: context,
            transform: transform,
            viewport: viewport
        };
        loaded_page.render(renderContext);
    }

    let expanded = false;

</script>
<section>

    {#await page}
        Loading page....pdf_wrapper
    {:then loaded_page}
        <div class="page_wrapper">
            <div class="page_header">
                <h2>{page_number + 1}.</h2>
                <small>of {total_pages}</small>
                <button class="expand_button ds-button-blue" on:click={() => expanded = !expanded}>
                    {#if expanded }
                    Collapse
                {:else}
                    Expand
                {/if}
                </button>
            </div>
            <div class="pdf_wrapper">
                <div data-expanded="{expanded}">
                    <canvas use:render_page={{loaded_page: loaded_page }}></canvas>
                </div>


            </div>
            <BallotPicker page_number="{page_number}"></BallotPicker>
        </div>

    {/await}
</section>
<hr>
<style>
    .page_wrapper {
        display: grid;
        grid-gap: 1em;
        grid-template-columns: 4em minmax(600px, 70%) minmax(20%, 300px);
        grid-template-areas:
            "page_header" "pdf_wrapper" "ballot-picker"
    }
    @media (max-width: 800px) {
        .page_wrapper {
            display: block;
        }
        .pdf_wrapper > div:not([data-expanded=true]) {
            max-height:200px;
            overflow: clip;
        }
        .page_header > * {
            display: inline-block;
            font-size: 1.2em !important;
            font-weight: normal;
        }
    }

    .page_wrapper > * {
        /*border: 1px solid red;*/
    }

    .pdf_wrapper {
        text-align: center;
    }

    .pdf_wrapper > div:not([data-expanded=true]) {
        height: 400px;
        overflow: clip;
    }
    .page_header {
        text-align: center;
    }
    .expand_button {
        margin: 0.5em 0;
        padding: 0.2em;
        font-size: 0.9em;
    }
</style>
