<script>
    import {BallotStore, PageStore} from './Store.js';

    export let page_number;

    function mark_ballot_for_page(event) {
        const ballot_id = event.target.dataset["ballot"];
        const page_num = event.target.dataset["page_number"];
        PageStore.update(pages => ({...pages, [page_num]: ballot_id}));
    }

    $: if (page_number > 0 && $PageStore[page_number - 1] === 'NOMATCH' && $PageStore[page_number] === 'CONTINUATION') {
        PageStore.update(pages => ({...pages, [page_number]: null}));
    }

</script>
<div class="ballot-picker">
    <fieldset>
        <legend>Related ballot</legend>
        <div class="ds-stack-smallest">
            {#if page_number > 0 && $PageStore[page_number - 1] !== 'NOMATCH'}
                <label class="ds-field-checkbox">
                    <input
                            type="radio"
                            data-ballot="CONTINUATION"
                            data-page_number="{page_number}"
                            name="ballot_for_page_{page_number}"
                            on:change={mark_ballot_for_page}
                            checked={$PageStore[page_number] === 'CONTINUATION'}
                    >
                    <span>Continuation page</span>
                </label>
            {/if}
            <label class="ds-field-checkbox">
                <input
                        type="radio"
                        data-ballot="NOMATCH"
                        data-page_number="{page_number}"
                        name="ballot_for_page_{page_number}"
                        on:change={mark_ballot_for_page}
                        checked={$PageStore[page_number] === 'NOMATCH'}
                >
                <span>No match</span>
            </label>
            <hr />

            {#each $BallotStore as {ballot_paper_id, label, disabled} (ballot_paper_id)}
                {#if !Object.values($PageStore).includes(ballot_paper_id) || $PageStore[page_number] === ballot_paper_id}
                    <label
                            class="ds-field-checkbox"
                            title={disabled ? "This ballot is matched to a page on another SOPN" : ""}
                    >

                        <input
                                type="radio"
                                data-ballot="{ballot_paper_id}"
                                data-page_number="{page_number}"
                                name="ballot_for_page_{page_number}"
                                on:change={mark_ballot_for_page}
                                checked={$PageStore[page_number] === ballot_paper_id}
                                disabled={disabled}
                        >
                        <span style={disabled ? "text-decoration: line-through;" : ""}>{label}</span>
                    </label>
                {/if}
            {/each}

        </div>
    </fieldset>
</div>

<style>
    .ds-scope .ds-field-checkbox:has(:disabled) span::before {
        background-color: lightgray;
    }
</style>
