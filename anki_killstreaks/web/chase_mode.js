let count = 0
const waitForPycmd = () => {
  if(typeof window.pycmd !== "undefined"){
    initializeChaseMode()
  }
  else {
    if (count < 10) {
      setTimeout(waitForPycmd, 100);
      count++;
    }
    else {
      console.log("timed out...")
    }
  }
}
waitForPycmd()

const initializeChaseMode = () => {
  pycmd("chaseModeLoaded")
}

const setChaseModeHTML = (html) => {
  console.log(html)
  $("#chase_mode").html(html)
}
