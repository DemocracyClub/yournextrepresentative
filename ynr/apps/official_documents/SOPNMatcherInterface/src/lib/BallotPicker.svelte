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
                <label class="ds-field-radio">
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
            <label class="ds-field-radio">
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

            {#each $BallotStore.filter(b => b.disabled === false) as {ballot_paper_id, label, disabled} (ballot_paper_id)}
                {#if !Object.values($PageStore).includes(ballot_paper_id) || $PageStore[page_number] === ballot_paper_id}
                    <label class="ds-field-radio">

                        <input
                                type="radio"
                                data-ballot="{ballot_paper_id}"
                                data-page_number="{page_number}"
                                name="ballot_for_page_{page_number}"
                                on:change={mark_ballot_for_page}
                                checked={$PageStore[page_number] === ballot_paper_id}
                        >
                        <span>{label}</span>
                    </label>
                {/if}
            {/each}

            {#if $BallotStore.filter(b => b.disabled === true).length > 0 }
                <hr />
                <div class="not-available">
                    Not available for matching
                    <ul>
                        {#each $BallotStore.filter(b => b.disabled === true) as {ballot_paper_id, label, disabled} (ballot_paper_id)}
                            <li>{label}</li>
                        {/each}
                    </ul>
                    These ballots are matched to a page on another SOPN
                </div>
            {/if}

        </div>
    </fieldset>
</div>

<style>
    .ds-field-radio {
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    .ds-field-radio input[type="radio"] {
        margin-top: 3px;
    }

    .not-available, .not-available * {
        color: #4d4d4d;
        font-size: .875rem;
    }

    .not-available ul {
        margin-top: 1.25rem;
    }
</style>
