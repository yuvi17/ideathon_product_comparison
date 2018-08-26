import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

function Card(props) {
    return  (

      <div class="card">
        <img src={props.image_url} />
        <br/>
        {props.name}
        <br/>
        {props.price}
        <br/>
        {props.unit}
      </div>

    );
};


class App extends React.Component {

  constructor(props) {
    super(props);

  };



  renderCard(data) {
    return
      <Card
        value = data

      />
  };
}

export default App;
