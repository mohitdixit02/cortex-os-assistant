# Context
This repo contains the UI code for the cortest-os-assitant app. This app involves a voice-based AI application that listens to user queries, and interactively responds using different tools. The UI is built as a desktop application.

## Tech Stack
1. Electron: For building the desktop application.
2. Next.js: For building the frontend interface.

## Current State
The UI is currently in the early stage of developement, suffecient enough to test with backend.

## Your Task
Your task is to develop the whole UI of the app, which must include the following features:

### Welcome Card on launch
As soon as the applicatino launches, there should be welcome cards with a series of 6-7 cards, each card having title, description and an icon/image. It should look like get-started cards.

### Landing Page
As soon as user lands, homepage must contain the main layout having a sidebar and main layout.
1. Sidebar: The sidebar should have the following options:
   - Home: Navigates to the homepage.
   - History: Displays the history of user interactions with the assistant.
   - Settings: Allows users to configure their preferences and settings for the assistant.
   - Profile: Displays user profile information and allows users to edit their profile details.

2. if user is not login, it must have feature to login/signup using google auth.
3. Main Layout: (On right side) Must have the Assistant inerface which can be a animated bubble or animation sphere that indicates the assistant is listening or processing. Below the bubble, there should be buttons to start conversation or stop conversation. Note that It is voice assistant, so implement accordingly.

### Settings
Must be a spearte page and have tuning features for the assistant, such as adjusting the voice, language, and other preferences. (You can create your own as of now for demonstration purposes)

### Profile
Must be a separate page that displays user profile information, such as name, email, and profile picture.
It should also user to see therir interaction history with the assistant, and allow them to edit their profile details.

### History
Must be a separate page that displays the history of user interactions with the assistant, in terms of session or conversation threads.

## Color Scheme and Design
Use Purple, red, blue gradient and dark theme to create a visually appealing and modern design for the UI. The design should be intuitive and user-friendly, ensuring that users can easily navigate through the different features and options available in the app. Use icons, framer-motion animations, and other visual elements to enhance the user experience and make the interface more engaging.

## Additional Libraries
You can use `framer-motion` for animations, `react-icons` for icons, and any other libraries that you find suitable for enhancing the UI and user experience.

# Important Notes
1. The UI should be responsive and work well on different screen sizes and resolutions (Desktop Application).
2. Ensure that you never touch any other code outside `app` directory.
3. Inside `app` directory, dont touch existing logic of Audio and Websocket files. You must have to create new files or change exisiting files only for UI related code. If you need to create new files, create them inside `app/components` directory.
4. Make sure to maintain a clean and organized code structure, following best practices for React and Next.js development.
5. Don't change anything in `audio` and `socket` directory.

Best of Luck!
