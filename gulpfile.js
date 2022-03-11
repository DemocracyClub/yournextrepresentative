var gulp = require('gulp');
var concat = require('gulp-concat');
var convertEncoding = require('gulp-convert-encoding');


const foundationDir = './node_modules/foundation-sites';
const jqueryDir = './node_modules/jquery';
const select2Dir = './node_modules/select2';
const sorttable = './node_modules/sorttable';

const paths = {
    foundation_js: [`${foundationDir}/scss/*`,`${foundationDir}/scss/*/**`,]
};



function jquery_js() {
    var paths = [
        `${jqueryDir}/dist/jquery.js`,
    ];
    return gulp.src(paths)
        .pipe(gulp.dest('ynr/assets/js/'))
}

function select2_js() {
    var paths = [
        `${select2Dir}/dist/js/select2.full.js`,
    ];
    return gulp.src(paths)
        .pipe(gulp.dest('ynr/assets/js/'))
}

function select2_css() {
    var paths = [
        `${select2Dir}/dist/css/select2.css`,
    ];
    return gulp.src(paths)
        .pipe(gulp.dest('ynr/assets/scss/'))
}

function foundation_js() {
    var paths = [
        `${foundationDir}/js/foundation.js`,
    ];
    return gulp.src(paths)
        .pipe(concat('foundation.js'))
        .pipe(gulp.dest('ynr/assets/js/'))
}

function foundation_scss() {
    var paths = [`${foundationDir}/scss/*`,`${foundationDir}/scss/*/**`,];
    return gulp.src(paths)
        .pipe(gulp.dest('ynr/assets/scss/'))
}

function sorttable_js() {
    var paths = [
        `${sorttable}/sorttable.js`,
    ];
    return gulp.src(paths)
        .pipe(convertEncoding({from: 'iso-8859-15', to: 'utf8'}))
        .pipe(gulp.dest('ynr/assets/js/'))
}

exports.default = gulp.series(
    jquery_js,
    select2_js,
    select2_css,
    foundation_scss,
    foundation_js, 
    sorttable_js,
);
