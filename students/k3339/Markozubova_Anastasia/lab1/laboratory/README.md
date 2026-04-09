# uvicorn app.main:app --reload
User -> Hackathon : один ко многим
Hackathon -> Team : один ко многим
Hackathon -> Task : один ко многим
Task -> Submission : один ко многим
Submission -> Review : один ко многим
User <-> Hackathon через HackathonRegistration : многие ко многим
User <-> Team через TeamMembership : многие ко многим