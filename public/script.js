document.getElementById('uploadForm').addEventListener('submit', async (event) => {
  event.preventDefault();

  document.getElementById('original-layout-image').src = "";
  document.getElementById('original-layout-image').alt = "";


  const files = document.getElementById('fileInput').files;
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  try {
    const response = await fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      // Show original design
      document.getElementById('original-design').style.display = "block";

      // Clear dropdown
      document.getElementById('feature-output').innerHTML = ""; 
      document.getElementById('random-feature-output').innerHTML = ""; 
      document.getElementById('randomized-design').style.display = "none"; 
      document.getElementById('detailed_placement').style.display = "none"; 
      document.getElementById('legalized-design').style.display = "none"; 


      // Reset dropdown values
      document.getElementById('features').value = ""; 
      document.getElementById('placement-algorithms').value = ""; 
      document.getElementById('random-features').value = ""; 
      document.getElementById('download-layout-btn').style.display = "none";
      document.getElementById('modify-node').style.display = "none";

      // Clear any input fields in modify-node form
      document.getElementById('modify-node-id').value = "";
      document.getElementById('modify-x').value = "";
      document.getElementById('modify-y').value = "";

      // Receive and display the image
      const blob = await response.blob();
      const imgUrl = URL.createObjectURL(blob);
      const imgElement = document.createElement('img');
      imgElement.src = imgUrl;
      imgElement.alt = 'Bookshelf Visualization';
      document.getElementById('result').innerHTML = ''; 
      document.getElementById('result').appendChild(imgElement);
    } else {
      const errorText = await response.json();
      document.getElementById('result').innerText = errorText.message;
    }
  } catch (error) {
    console.error('Error:', error);
    document.getElementById('result').innerText = 'An error occurred while processing the files.';
  }
});




//Dopdown menu
function onFeatureSelect() {
  const selectedFeature = document.getElementById("features").value;
  const outputDiv = document.getElementById("feature-output");
  const netSearchDiv = document.getElementById("net-search");
  const nodeSearchDiv = document.getElementById("node-search");
  const placementOptionsDiv = document.getElementById("placement-options");
  const modifyNodeDiv = document.getElementById("modify-node");


  const randomizedDesignSection = document.getElementById("randomized-design");
  randomizedDesignSection.style.display = "none"; 
  modifyNodeDiv.style.display = "none";
  document.getElementById("random-features").value = ""; 
  document.getElementById("random-feature-output").innerHTML = ""; 
  document.getElementById("placement-options").style.display = "none";
  document.getElementById("legalized-design").style.display = "none";
  document.getElementById("detailed_placement").style.display = "none";

  outputDiv.innerHTML = "";

  if (selectedFeature !== "global_placement") {
    document.getElementById("placement-algorithms").value = "";
  }

  if (selectedFeature === "total_wire_length") {
    netSearchDiv.style.display = "none";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none"; 
    fetch("http://localhost:5001/calculate_wire_length")
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        if (data.total_length !== undefined) {
          outputDiv.innerHTML = "Total Wire Length: " + data.total_length;
        } else if (data.error) {
          outputDiv.innerHTML = "Error: " + data.error;
        } else {
          outputDiv.innerHTML = "Unexpected response format.";
        }
      })
      .catch(error => {
        console.error("Error calculating wire length:", error);
        outputDiv.innerHTML = "Error calculating wire length. Check server logs for details.";
      });
  } else if (selectedFeature === "specific_net_length") {
    netSearchDiv.style.display = "block";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none"; 
    outputDiv.innerHTML = "";
  } else if (selectedFeature === "node_coordinates") {
    nodeSearchDiv.style.display = "block";
    netSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none"; 
    outputDiv.innerHTML = "";
  } else if (selectedFeature === "node_size_statistics") {
    netSearchDiv.style.display = "none";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none";
    fetch("http://localhost:5001/node_size_statistics")
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          outputDiv.innerHTML = `
            <h3>Node Size Statistics (Largest to Smallest):</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr>
                  <th style="border-bottom: 1px solid #ddd; padding: 8px; text-align: left;">Node ID</th>
                  <th style="border-bottom: 1px solid #ddd; padding: 8px; text-align: right;">Area</th>
                </tr>
              </thead>
              <tbody>
                ${data.map(node => `
                  <tr>
                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${node.node_id}</td>
                    <td style="border-bottom: 1px solid #ddd; padding: 8px; text-align: right;">${node.area}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        } else {
          outputDiv.innerHTML = "Unexpected response format.";
        }
      })
      .catch(error => {
        console.error("Error fetching node size statistics:", error);
        outputDiv.innerHTML = "Error fetching node size statistics. Check server logs for details.";
      });
  } else if (selectedFeature === "largest_smallest_nets_hpwl") {
    fetch("http://localhost:5001/largest_smallest_nets_hpwl")
      .then(response => response.json())
      .then(data => {
        if (data.largest_net && data.smallest_net) {
          outputDiv.innerHTML = `
            <div class="net-card">
            <h4>Largest Net by HPWL</h4>
            <p><strong>Net ID:</strong> ${data.largest_net.net_id}</p>
            <p><strong>HPWL:</strong> ${data.largest_net.hpwl}</p>
            <p><strong>Nodes:</strong> ${data.largest_net.nodes.join(', ')}</p>
          </div>
          <div class="net-card">
            <h4>Smallest Net by HPWL</h4>
            <p><strong>Net ID:</strong> ${data.smallest_net.net_id}</p>
            <p><strong>HPWL:</strong> ${data.smallest_net.hpwl}</p>
            <p><strong>Nodes:</strong> ${data.smallest_net.nodes.join(', ')}</p>
          </div>
        `;
        } else {
          outputDiv.innerHTML = "Unexpected response format.";
        }
      })
      .catch(error => {
        console.error("Error fetching largest and smallest nets by HPWL:", error);
        outputDiv.innerHTML = "Error fetching data. Check server logs for details.";
      });
  } else if (selectedFeature === "global_placement") {
    netSearchDiv.style.display = "none";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "block"; 
    outputDiv.innerHTML = ""; 
    document.getElementById("placement-options").style.display = "block";
  } else if (selectedFeature === "legalization") {
    fetch("http://localhost:5001/legalize_placement", {
      method: "POST",
    })
      .then(response => response.json())
      .then(data => {
        if (data.image_url) {
          document.getElementById("legalized-design").style.display = "block";
          document.getElementById("legalized-layout-image").src = data.image_url;
    
          let skippedText = "";
          if (data.skipped_nodes && data.skipped_nodes.length > 0) {
            skippedText = `<p><strong>Nodes left out:</strong> ${data.skipped_nodes.join(", ")}</p>`;
          }
    
          document.getElementById("feature-output").innerHTML = `
            <p>${data.message}</p>
            ${skippedText}
          `;
        } else if (data.error) {
          document.getElementById("feature-output").innerHTML = `<p>Error: ${data.error}</p>`;
        }
      })
      .catch(error => {
        console.error("Error during legalization:", error);
        document.getElementById("feature-output").innerHTML = "Error legalizing design.";
      });
  } else if (selectedFeature === "sorted_nets") {
    netSearchDiv.style.display = "none";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none"; 
    fetch("http://localhost:5001/sorted_nets")
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                outputDiv.innerHTML = `
                    <h3>Nets Sorted by Wirelength (Largest to Smallest):</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Net ID</th>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Wirelength</th>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Nodes</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(net => `
                                <tr>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.net_id}</td>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.hpwl}</td>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.nodes.join(", ")}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            } else if (data.error) {
                outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            } else {
                outputDiv.innerHTML = `<p>Unexpected response format.</p>`;
            }
        })
      .catch(error => {
        console.error("Error fetching sorted nets:", error);
        outputDiv.innerHTML = "Error fetching sorted nets. Check server logs for details.";
      });
  
    } else if (selectedFeature === "detailed_placement") {
  fetch("http://localhost:5001/detailed_placement", {
    method: "POST",
  })
    .then(response => response.json())
    .then(data => {
      if (data.image_url) {
        document.getElementById("detailed_placement").style.display = "block";
        document.getElementById("detailed-placement-image").src = data.image_url;
        outputDiv.innerHTML = `<p>${data.message}</p>`;
        if (data.failed_nodes && data.failed_nodes.length > 0) {
          outputDiv.innerHTML += `<p>Unplaced Nodes: ${data.failed_nodes.join(', ')}</p>`;
        }
      } else if (data.error) {
        outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
      }
    })
    .catch(error => {
      console.error("Error in detailed placement:", error);
      outputDiv.innerHTML = "Error performing detailed placement.";
    }); 
  } else if (selectedFeature === "legality_check") {
  fetch("http://localhost:5001/legality_check")
    .then(response => response.json())
    .then(data => {
      const summary = data.summary;
      outputDiv.innerHTML = `
        <h3>Random Design Legality Check Summary:</h3>
        <ul>
          <li><strong>Overlaps:</strong> ${summary.overlaps}</li>
          <li><strong>Misaligned Nodes:</strong> ${summary.misaligned}</li>
          <li><strong>Out of Bounds:</strong> ${summary.out_of_bounds}</li>
        </ul>
      `;
    })
    .catch(error => {
      console.error("Error fetching legality check results:", error);
      outputDiv.innerHTML = "Error performing legality check. Check server logs for details.";
    });
} else if (selectedFeature === "modify_node_placement") {
      modifyNodeDiv.style.display = "block";
      
      const modifyButton = document.querySelector("#modify-node button");
      modifyButton.addEventListener("click", function() {
        const nodeId = document.getElementById("modify-node-id").value;
        const newX = document.getElementById("modify-x").value;
        const newY = document.getElementById("modify-y").value;
  
        if (!nodeId || isNaN(newX) || isNaN(newY)) {
          outputDiv.innerHTML = "Please enter valid Node ID, X, and Y coordinates.";
          return;
        }
  
        fetch("http://localhost:5001/modify_node_coordinates", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            node_id: nodeId,
            x: newX,
            y: newY,
          }),
        })
          .then(response => response.json())
          .then(data => {
            if (data.image_url) {
              const layoutImage = document.getElementById("original-layout-image");
              const downloadButton = document.getElementById("download-layout-btn");

              layoutImage.src = data.image_url;
              outputDiv.innerHTML = `<p>${data.message}</p>`;

              // Show and enable the download button
              downloadButton.style.display = "inline-block";
              downloadButton.onclick = function () {
                const link = document.createElement("a");
                link.href = data.image_url;
                link.download = "updated_layout.png";
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              };
              let netList = "";
              if (data.affected_nets && data.affected_nets.length > 0) {
                netList = data.affected_nets.map(net =>
                  `<li><strong>${net.net_id}</strong>: ${net.length}</li>`
                ).join("");
              }

              outputDiv.innerHTML = `
                <p>${data.message}</p>
                <p><strong>Total Wirelength:</strong> ${data.updated_total_wirelength}</p>
                <h4>Affected Nets:</h4>
                <ul>${netList || "<li>None</li>"}</ul>
              `;
            } else if (data.error) {
              outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            }
          })
          .catch(error => {
            console.error("Error modifying node coordinates:", error);
            outputDiv.innerHTML = "Error modifying node coordinates. Check server logs for details.";
          });
      });
    } else {
    netSearchDiv.style.display = "none";
    nodeSearchDiv.style.display = "none";
    placementOptionsDiv.style.display = "none";
    outputDiv.innerHTML = "";
  }
}


function runPlacementAlgorithm() {
  const selectedAlgorithm = document.getElementById("placement-algorithms").value;
  const outputDiv = document.getElementById("feature-output");

  const randomizedDesignSection = document.getElementById("randomized-design");
  const randomFeaturesDropdown = document.getElementById("random-features");
  randomizedDesignSection.style.display = "none"; 
  randomFeaturesDropdown.value = ""; 
  document.getElementById("random-feature-output").innerHTML = ""; 

  if (selectedAlgorithm === "random") {
    fetch("http://localhost:5001/random_placement", { method: "POST" })
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          outputDiv.innerHTML = "<p>Random Placement applied successfully. Visualization updated.</p>";
          loadRandomVisualization();  
        } else {
          outputDiv.innerHTML = "Error applying random placement.";
        }
      })
      .catch(error => {
        console.error("Error running random placement:", error);
        outputDiv.innerHTML = "Error running random placement. Check server logs for details.";
      });
  } else {
    outputDiv.innerHTML = "<p>Selected placement algorithm not yet implemented.</p>";
  }
}



function calculateSpecificNetLength() {
  const netId = document.getElementById("net-id").value;
  const outputDiv = document.getElementById("feature-output");

  if (!netId) {
    outputDiv.innerHTML = "Please enter a valid Net ID.";
    return;
  }

  fetch(`http://localhost:5001/calculate_net_length/${netId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then(data => {
      if (data.wire_length !== undefined) {
        outputDiv.innerHTML = `Wire Length for Net ${netId}: ${data.wire_length}`;
      } else if (data.error) {
        outputDiv.innerHTML = "Error: " + data.error;
      } else {
        outputDiv.innerHTML = "Unexpected response format.";
      }
    })
    .catch(error => {
      console.error("Error calculating specific net length:", error);
      outputDiv.innerHTML = "Error calculating specific net length. Check server logs for details.";
    });
}

function getNodeCoordinates() {
  const nodeId = document.getElementById("node-id").value;
  const outputDiv = document.getElementById("feature-output");

  if (!nodeId) {
    outputDiv.innerHTML = "Please enter a valid Node ID.";
    return;
  }

  fetch(`http://localhost:5001/get_node_coordinates/${nodeId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then(data => {
      if (data.coordinates) {
        const { x, y } = data.coordinates;
        outputDiv.innerHTML = `Coordinates for Node ${nodeId}: x = ${x}, y = ${y}`;
      } else if (data.error) {
        outputDiv.innerHTML = "Error: " + data.error;
      } else {
        outputDiv.innerHTML = "Unexpected response format.";
      }
    })
    .catch(error => {
      console.error("Error fetching node coordinates:", error);
      outputDiv.innerHTML = "Error fetching node coordinates. Check server logs for details.";
    });
}


function loadRandomVisualization() {
  fetch("http://localhost:5001/random_visualize_layout")
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.blob();
    })
    .then(imageBlob => {
      const imgUrl = URL.createObjectURL(imageBlob);
      document.getElementById("random-layout-image").src = imgUrl;
      document.getElementById("randomized-design").style.display = "block";  
    })
    .catch(error => console.error("Error loading randomized visualization:", error));
}



function onRandomFeatureSelect() {
  const selectedFeature = document.getElementById("random-features").value;
  const outputDiv = document.getElementById("random-feature-output");

  document.getElementById("random-net-search").style.display = "none";
  document.getElementById("random-node-search").style.display = "none";
  document.getElementById("random-modify-node").style.display = "none";
  outputDiv.innerHTML = "";

  if (selectedFeature === "random_total_wire_length") {
    fetch("http://localhost:5001/random_calculate_wire_length")
      .then(response => response.json())
      .then(data => outputDiv.innerHTML = "Total Wire Length: " + data.total_length)
      .catch(error => console.error("Error:", error));
  } else if (selectedFeature === "random_specific_net_length") {
    document.getElementById("random-net-search").style.display = "block";
  } else if (selectedFeature === "random_node_coordinates") {
    document.getElementById("random-node-search").style.display = "block";
  } else if (selectedFeature === "random_largest_smallest_nets_hpwl") {
    fetch("http://localhost:5001/random_largest_smallest_nets_hpwl")
      .then(response => response.json())
      .then(data => {
        if (data.largest_net && data.smallest_net) {
          outputDiv.innerHTML = `
            <h3>Largest Net by HPWL</h3>
            <p><strong>Net ID:</strong> ${data.largest_net.net_id}</p>
            <p><strong>HPWL:</strong> ${data.largest_net.hpwl}</p>
            <p><strong>Nodes:</strong> ${data.largest_net.nodes.join(', ')}</p>

            <h3>Smallest Net by HPWL</h3>
            <p><strong>Net ID:</strong> ${data.smallest_net.net_id}</p>
            <p><strong>HPWL:</strong> ${data.smallest_net.hpwl}</p>
            <p><strong>Nodes:</strong> ${data.smallest_net.nodes.join(', ')}</p>
          `;
        } else {
          outputDiv.innerHTML = "Unexpected response format.";
        }
      })
      .catch(error => {
        console.error("Error fetching random largest and smallest nets by HPWL:", error);
        outputDiv.innerHTML = "Error fetching data. Check server logs for details.";
      });
  } else if (selectedFeature === "save_image") {
    saveRandomImage(); // Call the function to save the image
  } else if (selectedFeature === "random_legality_check") {
  fetch("http://localhost:5001/random_legality_check")
    .then(response => response.json())
    .then(data => {
      const summary = data.summary;
      outputDiv.innerHTML = `
        <h3>Random Design Legality Summary:</h3>
        <ul>
          <li><strong>Overlaps:</strong> ${summary.overlaps}</li>
          <li><strong>Misaligned:</strong> ${summary.misaligned}</li>
          <li><strong>Out of Bounds:</strong> ${summary.out_of_bounds}</li>
        </ul>
      `;
    })
    .catch(error => {
      console.error("Error fetching random legality check:", error);
      outputDiv.innerHTML = "Error checking legality for random design.";
    });
} else if (selectedFeature === "random_modify_node_placement") {
    document.getElementById("random-modify-node").style.display = "block";
  } else if (selectedFeature === "random_sorted_nets") {
    fetch("http://localhost:5001/random_sorted_nets")
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                outputDiv.innerHTML = `
                    <h3>Random Placement Nets Sorted by Wirelength (Largest to Smallest):</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Net ID</th>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Wirelength</th>
                                <th style="border-bottom: 1px solid #ddd; padding: 8px;">Nodes</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(net => `
                                <tr>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.net_id}</td>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.hpwl}</td>
                                    <td style="border-bottom: 1px solid #ddd; padding: 8px;">${net.nodes.join(", ")}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                `;
            } else if (data.error) {
                outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            } else {
                outputDiv.innerHTML = `<p>Unexpected response format.</p>`;
            }
        })
        .catch(error => {
            console.error("Error fetching sorted nets for random placement:", error);
            outputDiv.innerHTML = "<p>Error fetching sorted nets. Check server logs for details.</p>";
        }); 
  }
}

function modifyRandomNodePlacement() {
  const nodeId = document.getElementById("random-modify-node-id").value;
  const newX = document.getElementById("random-modify-x").value;
  const newY = document.getElementById("random-modify-y").value;
  const outputDiv = document.getElementById("random-feature-output");

  if (!nodeId || isNaN(newX) || isNaN(newY)) {
    outputDiv.innerHTML = "Please enter valid Node ID, X, and Y coordinates.";
    return;
  }

  fetch("http://localhost:5001/random_modify_node_coordinates", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      node_id: nodeId,
      x: newX,
      y: newY,
    }),
  })
    .then(response => response.json())
    .then(data => {
      if (data.image_url) {
        document.getElementById("random-layout-image").src = data.image_url; // Update the visualization
        outputDiv.innerHTML = `<p>${data.message}</p>`;
      } else if (data.error) {
        outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
      }
    })
    .catch(error => {
      console.error("Error modifying random node coordinates:", error);
      outputDiv.innerHTML = "Error modifying random node coordinates. Check server logs for details.";
    });
}


function calculateRandomSpecificNetLength() {
  const netId = document.getElementById("random-net-id").value;
  const outputDiv = document.getElementById("random-feature-output");

  if (!netId) {
    outputDiv.innerHTML = "Please enter a Net ID.";
    return;
  }

  fetch(`http://localhost:5001/random_calculate_net_length/${netId}`)
    .then(response => response.json())
    .then(data => {
      if (data.wire_length !== undefined) {
        outputDiv.innerHTML = `Wire Length for Net ${netId}: ${data.wire_length}`;
      } else if (data.error) {
        outputDiv.innerHTML = "Error: " + data.error;
      } else {
        outputDiv.innerHTML = "Unexpected response format.";
      }
    })
    .catch(error => {
      console.error("Error calculating specific net wire length:", error);
      outputDiv.innerHTML = "Error calculating specific net wire length. Check server logs for details.";
    });
}



function calculateRandomNodeCoordinates() {
  const nodeId = document.getElementById("random-node-id").value;
  const outputDiv = document.getElementById("random-feature-output");

  if (!nodeId) {
    outputDiv.innerHTML = "Please enter a Node ID.";
    return;
  }

  fetch(`http://localhost:5001/random_node_coordinates?node_id=${nodeId}`)
    .then(response => response.json())
    .then(data => {
      if (data.x !== undefined && data.y !== undefined) {
        outputDiv.innerHTML = `Coordinates for Node ${nodeId}: X = ${data.x}, Y = ${data.y}`;
      } else if (data.error) {
        outputDiv.innerHTML = "Error: " + data.error;
      } else {
        outputDiv.innerHTML = "Unexpected response format.";
      }
    })
    .catch(error => {
      console.error("Error fetching node coordinates:", error);
      outputDiv.innerHTML = "Error fetching node coordinates. Check server logs for details.";
    });
}


function saveRandomImage() {
  fetch("http://localhost:5001/random_visualize_layout")
    .then(response => response.blob()) 
    .then(blob => {
      const url = URL.createObjectURL(blob); 
      const link = document.createElement("a"); 
      link.href = url;
      link.download = "random_placement_image.png"; 
      link.click(); 
      URL.revokeObjectURL(url); 
    })
    .catch(error => console.error("Error downloading image:", error));
}
