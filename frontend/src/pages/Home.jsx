import "../App.css";

function Home() {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>SpillTrace Dashboard</h2>
          <p>Monitor and investigate environmental spill incidents.</p>
        </div>

        <button className="upload-button">
          Upload Spill Data
        </button>
      </div>

    </div>
  );
}

export default Home;
