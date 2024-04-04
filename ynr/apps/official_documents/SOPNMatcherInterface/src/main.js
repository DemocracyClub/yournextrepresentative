import App from './App.svelte'

var dummy_data = {
    sopn_pdf: "https://s3.eu-west-2.amazonaws.com/static-candidates.democracyclub.org.uk/media/official_documents/local.gosport.forton.2022-05-05/statement-of-persons-nominated.pdf",
    ballots: [
        {'ballot_paper_id': 'local.gosport.alverstoke.2022-05-05', 'label': 'Alverstoke'},
        {'ballot_paper_id': 'local.gosport.anglesey.2022-05-05', 'label': 'Anglesey'},
        {'ballot_paper_id': 'local.gosport.bridgemary.2022-05-05', 'label': 'Bridgemary'},
        {'ballot_paper_id': 'local.gosport.brockhurst-privett.2022-05-05', 'label': 'Brockhurst & Privett'},
        {'ballot_paper_id': 'local.gosport.elson.2022-05-05', 'label': 'Elson'},
        {'ballot_paper_id': 'local.gosport.forton.2022-05-05', 'label': 'Forton'},
        {'ballot_paper_id': 'local.gosport.grange-alver-valley.2022-05-05', 'label': 'Grange & Alver Valley'},
        {'ballot_paper_id': 'local.gosport.harbourside-town.2022-05-05', 'label': 'Harbourside & Town'},
        {'ballot_paper_id': 'local.gosport.hardway.2022-05-05', 'label': 'Hardway'},
        {'ballot_paper_id': 'local.gosport.lee-east.2022-05-05', 'label': 'Lee East'},
        {'ballot_paper_id': 'local.gosport.leesland-newtown.2022-05-05', 'label': 'Leesland & Newtown'},
        {'ballot_paper_id': 'local.gosport.lee-west.2022-05-05', 'label': 'Lee West'},
        {'ballot_paper_id': 'local.gosport.peel-common.2022-05-05', 'label': 'Peel Common'},
        {'ballot_paper_id': 'local.gosport.rowner-holbrook.2022-05-05', 'label': 'Rowner & Holbrook'},
    ]
}

var page_data = document.getElementById("sopn-matcher-index-props")
var data;
if (!page_data) {
    data = dummy_data
} else {
    data = JSON.parse(page_data.textContent)
}

const app = new App({
    target: document.querySelector('#sopn-matcher-index-target'),
    props: data,
})
export default app
