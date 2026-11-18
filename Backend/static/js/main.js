/* =========================================================
   HOME PAGE CAROUSELS
========================================================= */

document.querySelectorAll(".genre-row").forEach((row) => {

    const grid = row.querySelector(".movie-grid");
    const leftBtn = row.querySelector(".scroll-btn.left");
    const rightBtn = row.querySelector(".scroll-btn.right");

    // Skip this section if anything is missing
    if (!grid || !leftBtn || !rightBtn) {
        console.log("Missing element in section:", row);
        return;
    }

    function updateButtons() {

        leftBtn.disabled = grid.scrollLeft <= 5;

        rightBtn.disabled =
            grid.scrollLeft + grid.clientWidth >=
            grid.scrollWidth - 5;
    }

    leftBtn.addEventListener("click", () => {

        grid.scrollBy({
            left: -900,
            behavior: "smooth"
        });

    });

    rightBtn.addEventListener("click", () => {

        grid.scrollBy({
            left: 900,
            behavior: "smooth"
        });

    });

    grid.addEventListener("scroll", updateButtons);

    updateButtons();
});


/* =========================================================
   MOOD RESULTS CAROUSEL
========================================================= */

function scrollMovies(direction) {

    const carousel = document.getElementById("movieCarousel");

    if (!carousel) {
        console.log("Mood movie carousel not found.");
        return;
    }

    /*
       Move approximately one screen of movie cards.

       clientWidth = visible width of the carousel.
       This means the arrow works properly regardless
       of the user's screen size.
    */

    const scrollAmount = carousel.clientWidth * 0.85;

    carousel.scrollBy({
        left: direction * scrollAmount,
        behavior: "smooth"
    });

    /*
       Update arrow state after the smooth scroll.
    */

    setTimeout(updateMoodCarouselButtons, 350);
}


/* =========================================================
   MOOD CAROUSEL ARROW STATE
========================================================= */

function updateMoodCarouselButtons() {

    const carousel = document.getElementById("movieCarousel");
    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");

    if (!carousel || !prevButton || !nextButton) {
        return;
    }

    /*
       Disable LEFT when we are at the beginning.
    */

    prevButton.disabled = carousel.scrollLeft <= 5;

    /*
       Disable RIGHT when we are at the end.
    */

    nextButton.disabled =
        carousel.scrollLeft + carousel.clientWidth >=
        carousel.scrollWidth - 5;
}


/* =========================================================
   INITIALIZE MOOD CAROUSEL
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const carousel = document.getElementById("movieCarousel");

    if (!carousel) {
        return;
    }

    const prevButton = document.getElementById("prevButton");
    const nextButton = document.getElementById("nextButton");

    if (!prevButton || !nextButton) {
        console.log("Mood carousel buttons not found.");
        return;
    }

    /*
       Keep buttons updated when the user:
       - clicks arrows
       - drags the carousel
       - resizes the browser
    */

    carousel.addEventListener(
        "scroll",
        updateMoodCarouselButtons
    );

    window.addEventListener(
        "resize",
        updateMoodCarouselButtons
    );

    /*
       Set initial state.
    */

    updateMoodCarouselButtons();

});


/* =========================================================
   NEW PICKS
========================================================= */

/* =========================================================
   NEW PICKS
========================================================= */

function getNewPicks() {

    /*
       Get the current mood directly from
       the current URL.
    */

    const currentUrl =
        new URL(window.location.href);

    const mood =
        currentUrl.searchParams.get("mood");


    /*
       Make sure we are actually on a
       mood-results page with a mood.
    */

    if (!mood) {

        console.log(
            "Mood not found in URL."
        );

        return;
    }


    /*
       Find the New Picks button.

       Supports both:
       .new-picks-button
       and
       #newPicksButton
    */

    const button =
        document.querySelector(
            ".new-picks-button"
        ) ||
        document.getElementById(
            "newPicksButton"
        );


    /*
       Prevent double clicking.
    */

    if (
        button &&
        button.dataset.loading === "true"
    ) {

        return;
    }


    /*
       Show loading state.
    */

    if (button) {

        button.dataset.loading =
            "true";

        button.innerHTML =
            "↻ Finding new picks...";

        button.style.pointerEvents =
            "none";

        button.style.opacity =
            "0.65";
    }


    /*
       Generate a completely NEW seed.

       Flask uses this seed inside:

       get_personalized_mood_movies()

       so a different seed produces
       different randomized recommendations.
    */

    const newSeed =
        Math.floor(
            Math.random() * 999999999
        );


    /*
       IMPORTANT:

       Keep the current mood.

       Example:

       mood=cozy

       remains:

       mood=cozy

       Only the refresh seed changes.
    */

    currentUrl.searchParams.set(
        "mood",
        mood
    );


    currentUrl.searchParams.set(
        "refresh",
        newSeed
    );


    /*
       Reload the current mood-results
       page with the new seed.
    */

    window.location.href =
        currentUrl.toString();
}


/* =========================================================
   TRAILER POPUP
========================================================= */

const playTrailerBtn =
    document.getElementById("playTrailerBtn");

const trailerModal =
    document.getElementById("trailerModal");

const trailerFrame =
    document.getElementById("trailerFrame");

const closeTrailer =
    document.getElementById("closeTrailer");


if (playTrailerBtn && trailerModal) {

    playTrailerBtn.addEventListener("click", function () {

        const trailerKey =
            this.dataset.trailer;

        if (!trailerKey) {

            alert("Trailer not available.");

            return;
        }

        trailerFrame.src =
            `https://www.youtube.com/embed/${trailerKey}?autoplay=1`;

        trailerModal.style.display = "flex";

    });


    if (closeTrailer) {

        closeTrailer.addEventListener("click", function () {

            trailerModal.style.display = "none";

            trailerFrame.src = "";

        });

    }


    trailerModal.addEventListener("click", function (e) {

        if (e.target === trailerModal) {

            trailerModal.style.display = "none";

            trailerFrame.src = "";

        }

    });

}


/* =========================================================
   WATCHLIST FLASH MESSAGE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const flashMessages =
            document.querySelectorAll(
                ".flash-message"
            );

        flashMessages.forEach(function (message) {

            setTimeout(function () {

                message.classList.add("hide");

                setTimeout(function () {

                    message.remove();

                }, 500);

            }, 4000);

        });

    }
);