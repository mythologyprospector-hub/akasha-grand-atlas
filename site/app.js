const searchInput = document.getElementById("q")
const categoryFilter = document.getElementById("categoryFilter")
const statusFilter = document.getElementById("statusFilter")
const freeOnly = document.getElementById("freeOnly")

const cards = Array.from(document.querySelectorAll(".card"))

function getBadges(card){

let badges = card.querySelector(".badges")

if(!badges) return []

return badges.innerText.toLowerCase().split("·").map(x=>x.trim())

}

function applyFilters(){

let q = searchInput.value.toLowerCase().trim()
let cat = categoryFilter.value
let status = statusFilter.value
let free = freeOnly.checked

let visible = 0

for(let card of cards){

let search = card.dataset.search || ""
let category = card.dataset.category || ""
let stat = card.dataset.status || ""

let badges = getBadges(card)

let matchSearch = !q || search.includes(q)

let matchCategory = !cat || category === cat

let matchStatus = !status || stat === status

let matchFree = !free || badges.includes("free")

if(matchSearch && matchCategory && matchStatus && matchFree){

card.style.display = ""

visible++

}else{

card.style.display = "none"

}

}

}

searchInput.addEventListener("input", applyFilters)
categoryFilter.addEventListener("change", applyFilters)
statusFilter.addEventListener("change", applyFilters)
freeOnly.addEventListener("change", applyFilters)

applyFilters()