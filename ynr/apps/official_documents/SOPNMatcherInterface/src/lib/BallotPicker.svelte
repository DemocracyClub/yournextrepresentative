<script>
    import {BallotStore} from './Store.js';

    export let page_number;

    function mark_ballot_for_page(event) {
        let ballot_id = event.target.dataset["ballot"];
        let page_number = event.target.dataset["page_number"];
        BallotStore.update(ballots => {
            const index = ballots.findIndex(ballot => ballot.ballot_paper_id === ballot_id);
            if (index !== -1) {
                let checked = event.target.checked
                ballots[index].matched = checked;
                var other_checkboxes = event.target.parentElement.parentElement.querySelectorAll('input')
                if (checked) {
                    ballots[index].matched_page = page_number;
                    other_checkboxes.forEach(el => {
                        if (!el.checked) {
                            el.disabled = true;
                        }
                    })
                } else {
                    ballots[index].matched_page = undefined;
                    other_checkboxes.forEach(el => {
                        el.disabled = false;
                    })
                }
            }
            return ballots;
        });

    }

</script>
<div class="ballot-picker">
    <fieldset>
        <legend>Related ballot</legend>
        <div class="ds-stack-smallest">
            {#each $BallotStore as {ballot_paper_id, label, matched_page, matched} (ballot_paper_id)}
                {#if !matched_page || (matched_page && matched_page == page_number)}
                    <label class="ds-field-checkbox">
                        <input
                                type="checkbox"
                                data-ballot="{ballot_paper_id}"
                                data-page_number="{page_number}"
                                name="ballot_for_page_{page_number}"
                                on:change={mark_ballot_for_page}
                                bind:checked={matched}
                        >
                        <span>{label}</span>
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
