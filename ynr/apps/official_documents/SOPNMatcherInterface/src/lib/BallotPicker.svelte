<script>
    import {BallotStore} from './Store.js';
    import {onMount, afterUpdate} from 'svelte';

    export let page_number;

    function updateDisabledStates() {
        const checkboxes = document.querySelectorAll(`input[name="ballot_for_page_${page_number}"]`);
        const anyChecked = Array.from(checkboxes).some(cb => cb.checked);

        checkboxes.forEach(checkbox => {
            const ballot_id = checkbox.dataset["ballot"];
            const ballot = $BallotStore.find(b => b.ballot_paper_id === ballot_id);
            
            // Never enable if the ballot has disabled property set to true
            if (ballot?.disabled) {
                checkbox.disabled = true;
            } else if (anyChecked) {
                checkbox.disabled = !checkbox.checked;
            } else {
                checkbox.disabled = false;
            }
        });
    }

    onMount(() => {
        updateDisabledStates();
    });

    afterUpdate(() => {
        updateDisabledStates();
    });

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
                        const el_ballot_id = el.dataset["ballot"];
                        const el_ballot = ballots.find(b => b.ballot_paper_id === el_ballot_id);
                        // Don't enable if the ballot has disabled property
                        if (!el_ballot?.disabled) {
                            el.disabled = false;
                        }
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
            {#each $BallotStore as {ballot_paper_id, label, matched_page, matched, disabled} (ballot_paper_id)}
                {#if !matched_page || (matched_page && matched_page == page_number)}
                    <label
                            class="ds-field-checkbox"
                            title={disabled ? "This ballot is matched to a page on another SOPN" : ""}
                    >

                        <input
                                type="checkbox"
                                data-ballot="{ballot_paper_id}"
                                data-page_number="{page_number}"
                                name="ballot_for_page_{page_number}"
                                on:change={mark_ballot_for_page}
                                bind:checked={matched}
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
