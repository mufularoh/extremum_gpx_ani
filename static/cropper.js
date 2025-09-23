/**
    * @typedef {{
        file_name: string,
        unique_id: string,
        document_id: string,
        segments: Segment[],
        track_id: number
    * }} Track
    * @typedef {[number, number][]} Segment
*/

/** 
    * @param {string} id
    * @returns HTMLElement
*/
const byId = (id) => {
    const ret = /** @type {HTMLElement | null} */ (document.getElementById(id));
    if (!ret) {
        throw new Error(`${id} not found!`);
    }
    return ret;
}
/** 
    * @param {string} id
    * @returns HTMLInputElement
*/
const byIdInp = (id) => {
    const ret = /** @type {HTMLInputElement | null} */ (document.getElementById(id));
    if (!ret) {
        throw new Error(`${id} not found!`);
    }
    return ret;

}

class TrackManager {
    /** @type HTMLElement */
    map;
    /** @type HTMLElement */
    list;
    /** @type HTMLElement */
    controls;

    /** @type Track[] */
    tracks;

    /** @type {number} */
    selectedIndex;

    /** @type {[number, number][]} */
    flatPoints;

    /** @type {number} */
    startIndex;

    /** @type {number}  */
    endIndex;

    /** @type {SVGCircleElement | null} */
    startCircle;

    /** @type {SVGCircleElement | null} */
    endCircle;

    /** @type {HTMLInputElement} */
    startPosition;
    /** @type {HTMLInputElement} */
    endPosition;

    /** @type {boolean} */
    inited;

    /** @type {HTMLElement} */
    saveButton;

    /** @type {HTMLElement} */
    cropButton;

    /** @type {HTMLElement} */
    resetButton;

    /** @type {string[]} */
    cropped;

    /** @type {HTMLElement} */
    loader;


    constructor() {
        this.map = byId("map");
        this.list = byId("tracks_list");
        this.controls = byId("controls");

        this.startPosition = byIdInp("start_position");
        this.endPosition = byIdInp("end_position");

        /** @param {InputEvent} e */
        const onInput = (e) => {
            const target = /** @type {HTMLInputElement | null} */ (e.target);
            if (target) {
                this.onInput(target);
            }
            this.applyButtons();
        };

        this.startPosition.addEventListener("input", onInput);
        this.endPosition.addEventListener("input", onInput);

        this.tracks = [];
        this.inited = false;

        this.list.addEventListener("click", (e) => {
            const target = /** @type {HTMLDivElement | null} */ (e.target);
            if (target?.classList.contains("track-item")) {
                const index = parseInt(target.getAttribute("data-index") ?? "0");
                this.inited = false;
                this.select(index);
            }
        });

        this.cropped = [];
        this.cropButton = byId("cut_button");
        this.saveButton = byId("download_button");
        this.resetButton = byId("reset_button");
        this.loader = byId("loader")

        this.cropButton.addEventListener("click", () => {
            this.cropTrack();
        });
        this.saveButton.addEventListener("click", () => {
            this.downloadTrack();
        });
        this.resetButton.addEventListener("click", () => {
            this.resetTrack();
        });
    }
    /** @param {Track[]} tracks */
    onLoad(tracks) {
        this.tracks = tracks;
        this.cropped = [];
        if (this.tracks.length) {
            this.select(0);
        } else {
            this.printEmpty();
        }
    }

    /** @param {HTMLInputElement} input */
    onInput(input) {
        if (this.inited) {
            const val = parseInt(input.value);
            const id = input.getAttribute("id") ?? "";

            if (id == "start_position") {
                this.startIndex = Math.max(0, Math.min(val, this.endIndex));
                if (this.startIndex != val) {
                    input.setAttribute("value", this.startIndex.toString());
                }
            } else {
                this.endIndex = Math.min(this.flatPoints.length - 1, Math.max(this.startIndex, val));
                if (this.endIndex != val) {
                    input.setAttribute("value", this.endIndex.toString());
                }
            }

            this.alignCircles();

        }
    }

    /** @param {number} index */
    select(index) {
        this.selectedIndex = Math.max(0, Math.min(this.tracks.length - 1, index));
        this.flatPoints = [];
        for (const segment of this.tracks[this.selectedIndex].segments) {
            for (const point of segment) {
                this.flatPoints.push(point);
            }
        }
        this.startIndex = 0;
        this.endIndex = this.flatPoints.length - 1;

        this.startPosition.setAttribute("max", this.endIndex.toString());
        this.endPosition.setAttribute("max", this.endIndex.toString());

        this.startPosition.value = "0";
        this.endPosition.value = this.endIndex.toString();
        this.inited = false;
        this.print();
    }

    printTracks() {
        /** @type {string[]} */
        const result = [];
        for (let i = 0; i < this.tracks.length; ++i) {
            result.push(`<div class="track-item${i == this.selectedIndex ? ' selected' : ''}" data-index="${i}">
                ${this.tracks[i].file_name}
            </div>`);
        }
        this.list.innerHTML = result.join("");
    }

    print() {
        this.printTracks();
        this.drawSelectedTrack();
    }

    drawSelectedTrack() {
        const track = this.tracks[this.selectedIndex];
        const svg = ["<svg version=\"1.1\" width=\"100\" height=\"100\" viewBox=\"0 0 100 100\" xmlns=\"http://www.w3.org/2000/svg\">"];
        let endIndex = 0;
        for (let j = 0; j < track.segments.length; ++j) {
            const segment = track.segments[j];
            if (segment.length) {
                /** @type {string[]} */
                const points = [];
                for (let i = 0; i < segment.length; i++) {
                    points.push(`${i == 0 ? 'M' : 'L'} ${segment[i][0]} ${100 - segment[i][1]}`);
                    endIndex++;
                }
                svg.push(`<path d="${points.join(" ")}" fill="transparent" stroke="#0d47a1" />`);
            }
        }
        svg.push("<circle cx=\"5\" cy=\"5\" r=\"1.5\" fill=\"#bf360c\" id=\"start_point\" />")
        svg.push("<circle cx=\"90\" cy=\"90\" r=\"1.5\" fill=\"#1b5e20\" id=\"end_point\" />")
        svg.push("</svg>");
        this.map.innerHTML = svg.join("");

        this.startCircle = /** @type {SVGCircleElement | null} */ this.map.querySelector("#start_point");
        this.endCircle = /** @type {SVGCircleElement | null} */ this.map.querySelector("#end_point");

        this.alignCircles();
        this.applyButtons();
        this.inited = true;
        this.controls.classList.add("loaded")
    }

    applyButtons() {
        const cutEnabled = (this.startIndex > 0 || this.endIndex < this.flatPoints.length - 1) && this.inited;
        if (cutEnabled) {
            this.cropButton.removeAttribute("disabled");
        } else {
            this.cropButton.setAttribute("disabled", "true");
        }
        const saveEnabled = this.cropped.includes(this.tracks[this.selectedIndex].unique_id);
        if (saveEnabled) {
            this.saveButton.removeAttribute("disabled");
        } else {
            this.saveButton.setAttribute("disabled", "true");
        }
    }

    resetTrack() {
        if (!this.inited) {
            return;
        }
        this.inited = false;
        this.loader.classList.add("visible");
        fetch(`/reset/${this.tracks[this.selectedIndex].track_id}/`, {
        }).then((d) => {
            if (d.ok) {
                d.json().then((x) => {
                    /** @type {Track} */
                    const track = x;
                    this.tracks[this.selectedIndex] = track;
                    this.cropped = this.cropped.filter((x) => x != track.unique_id);
                    this.loader.classList.remove("visible");
                    this.select(this.selectedIndex);
                });
            } else {
                d.text().then((x) => {
                    alert(x);
                    this.inited = true;
                    this.loader.classList.remove("visible");
                })
            }
        }).catch((err) => {
            alert(err);
            this.inited = true;
            this.loader.classList.remove("visible");
        });
    }

    cropTrack() {
        if (!this.inited) {
            return;
        }
        this.inited = false;
        this.loader.classList.add("visible");
        fetch("/crop/", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_id: this.tracks[this.selectedIndex].track_id,
                start_index: this.startIndex,
                end_index: this.endIndex
            })
        }).then((d) => {
            if (d.ok) {
                d.json().then((x) => {
                    /** @type {Track} */
                    const track = x;
                    this.tracks[this.selectedIndex] = track;
                    this.cropped.push(track.unique_id);
                    this.loader.classList.remove("visible");
                    this.select(this.selectedIndex);
                });
            } else {
                d.text().then((x) => {
                    alert(x);
                    this.inited = true;
                    this.loader.classList.remove("visible");
                })
            }
        }).catch((err) => {
            alert(err);
            this.inited = true;
            this.loader.classList.remove("visible");
        });
    }

    downloadTrack() {
        if (!this.inited || !this.cropped.includes(this.tracks[this.selectedIndex].unique_id)) {
            return;
        }
        try {
            window.Telegram?.WebApp.downloadFile({
                url: `/download/${this.tracks[this.selectedIndex].track_id}/`,
                file_name: this.tracks[this.selectedIndex].file_name
            });
        } catch {
            window.open(`/download/${this.tracks[this.selectedIndex].track_id}/`, "_blank");
        }
    }

    alignCircles() {
        if (!this.startCircle || !this.endCircle) {
            return;
        }
        const startCoord = this.flatPoints[this.startIndex];
        const endCoord = this.flatPoints[this.endIndex];

        this.startCircle.setAttribute("cx", `${startCoord[0]}`);
        this.startCircle.setAttribute("cy", `${100 - startCoord[1]}`);

        this.endCircle.setAttribute("cx", `${endCoord[0]}`);
        this.endCircle.setAttribute("cy", `${100 - endCoord[1]}`);
    }

    printEmpty() {
        this.map.innerHTML = "<div class='empty'>Нет загруженных треков!</div>"
        this.list.innerHTML = "";
    }
};



document.addEventListener("readystatechange", () => {
    if (document.readyState == "complete") {
        const userId = window.Telegram?.WebApp.initDataUnsafe.user?.id ?? 204668047;
        if (window.Telegram) {
            try {
                window.Telegram.WebApp.requestFullscreen();
            } catch { }
        }
        const manager = new TrackManager();
        if (userId) {
            fetch(`/tracks/${userId}/`, {
                method: "GET",
            }).then((resp) => {
                if (resp.ok) {
                    resp.json().then((d) => manager.onLoad(d.tracks));
                } else {
                    alert("Что-то сломалось!");
                }
            }).catch((err) => {
                console.error(err.toString ? err.toString : `${err}`);
            });
        }
    }
});
